#!/usr/bin/env python
"""Utility functions for websmash"""
import os

from flask import request
from os import path

import werkzeug.utils
from antismash_models import SyncJob as Job

from websmash import app, get_db
from websmash.error_handlers import BadRequest
from websmash.models import _generate_jobid


DEFAULT_QUEUE = 'jobs:queued'
FAST_QUEUE = 'jobs:minimal'
WAITLIST_PREFIX = 'jobs:waiting'
PRIORITY_QUEUE = 'jobs:priority'


def generate_confirmation_mail(message):
    """Generate confirmation email message from template"""
    confirmation_template = """We have received your feedback to antiSMASH and will reply to you as soon as possible.
Your message was:

%s
"""
    return confirmation_template % message


def _add_to_queue(redis_store, queue, job):
    """Add job to a specified job queue"""
    job.commit()
    redis_store.lpush(queue, job.job_id)


def _submit_job(redis_store, job, limit, vips):
    """Submit a new job"""
    job.state = 'queued'
    if job.email in vips:
        _add_to_queue(redis_store, PRIORITY_QUEUE, job)
    elif job.minimal:
        _add_to_queue(redis_store, FAST_QUEUE, job)
    else:
        if job.email:
            if _count_pending_jobs_with_email(redis_store, job) > limit:
                _waitlist_job(redis_store, job, job.email)
                return
        elif _count_pending_jobs_with_ip(redis_store, job) > limit:
            _waitlist_job(redis_store, job, job.ip_addr)
            return

        _add_to_queue(redis_store, DEFAULT_QUEUE, job)


def _count_pending_jobs_with_email(redis_store, job):
    """Count how many jobs are pending for the email of the current job"""
    count = 0
    for job_id in redis_store.lrange(DEFAULT_QUEUE, 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'email') == job.email:
            count += 1

    return count


def _count_pending_jobs_with_ip(redis_store, job):
    """Count how many jobs are pending for the IP address of the current job"""
    count = 0
    for job_id in redis_store.lrange(DEFAULT_QUEUE, 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'ip_addr') == job.ip_addr:
            count += 1

    return count


def _waitlist_job(redis_store, job, attribute):
    """Put the given job on a waitlist"""
    job.state = 'waiting'
    job.status = 'waiting: Too many jobs in queue for this user.'
    waitlist = '{}:{}'.format(WAITLIST_PREFIX, attribute)
    _add_to_queue(redis_store, waitlist, job)


def _get_checkbox(req, name):
    """Get True/False value for the checkbox of a given name"""
    str_value = req.form.get(name, u'off')
    return str_value == u'on' or str_value == 'true'


def dispatch_job():
    """Internal helper to dispatch a new job"""
    redis_store = get_db()
    taxon = app.config['TAXON']
    job_id = _generate_jobid(taxon)

    job = Job(redis_store, job_id)

    if 'X-Forwarded-For' in request.headers:
        job.ip_addr = request.headers.getlist("X-Forwarded-For")[0].rpartition(' ')[-1]
    else:
        job.ip_addr = request.remote_addr or 'untrackable'

    ncbi = request.form.get('ncbi', '').strip()

    val = request.form.get('email', '').strip()
    if val:
        job.email = val

    job.minimal = _get_checkbox(request, 'minimal')

    job.all_orfs = _get_checkbox(request, 'all_orfs')

    job.smcogs = _get_checkbox(request, 'smcogs')

    job.clusterblast = _get_checkbox(request, 'clusterblast')
    job.knownclusterblast = _get_checkbox(request, 'knownclusterblast')
    job.subclusterblast = _get_checkbox(request, 'subclusterblast')

    job.jobtype = 'antismash4'

    job.full_hmmer = _get_checkbox(request, 'fullhmmer')

    job.genefinder = request.form.get('genefinder', 'prodigal')

    val = request.form.get('from', 0, type=int)
    if val:
        job.from_pos = val

    val = request.form.get('to', 0, type=int)
    if val:
        job.to_pos = val

    job.inclusive = _get_checkbox(request, 'inclusive')
    job.cf_cdsnr = request.form.get('cf_cdsnr', 5, type=int)
    job.cf_npfams = request.form.get('cf_npfams', 5, type=int)
    job.cf_threshold = request.form.get('cf_threshold', 0.6, type=float)

    job.borderpredict = _get_checkbox(request, 'borderpredict')

    job.asf = _get_checkbox(request, 'asf')
    job.tta = _get_checkbox(request, 'tta')
    job.transatpks_da = _get_checkbox(request, 'transatpks_da')
    job.cassis = _get_checkbox(request, 'cassis')

    dirname = path.join(app.config['RESULTS_PATH'], job.job_id)
    os.mkdir(dirname)

    if ncbi != '':
        if ' ' in ncbi:
            raise BadRequest("Spaces are not allowed in an NCBI ID.")
        job.download = ncbi
    else:
        upload = request.files['seq']

        if upload is not None:
            filename = secure_filename(upload.filename)
            upload.save(path.join(dirname, filename))
            if not path.exists(path.join(dirname, filename)):
                raise BadRequest("Could not save file!")
            job.filename = filename
        else:
            raise BadRequest("Uploading input file failed!")

        if 'gff3' in request.files:
            gff_upload = request.files['gff3']
            if gff_upload is not None:
                gff_filename = secure_filename(gff_upload.filename)
                gff_upload.save(path.join(dirname, gff_filename))
                if not path.exists(path.join(dirname, gff_filename)):
                    raise BadRequest("Could not save GFF file!")
                job.gff3 = gff_filename

    _submit_job(redis_store, job, app.config['MAX_JOBS_PER_USER'], app.config['VIP_USERS'])
    return job


def secure_filename(name):
    """Even more secure filenames"""
    secure_name = werkzeug.utils.secure_filename(name)
    secure_name = secure_name.lstrip('-')
    return secure_name
