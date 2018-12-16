#!/usr/bin/env python
"""Utility functions for websmash"""
import os
import shutil

from flask import request
from os import path
import random
import uuid

import werkzeug.utils
from antismash_models import SyncJob as Job

from websmash import app, get_db
from websmash.error_handlers import BadRequest


def generate_confirmation_mail(message):
    """Generate confirmation email message from template"""
    confirmation_template = """We have received your feedback to antiSMASH and will reply to you as soon as possible.
Your message was:

%s
"""
    return confirmation_template % message


def _generate_jobid(taxon):
    """Generate a job uid based on the taxon"""
    return "{}-{}".format(taxon, uuid.uuid4())


def _add_to_queue(redis_store, queue, job):
    """Add job to a specified job queue"""
    job.commit()
    redis_store.lpush(queue, job.job_id)


def _submit_job(redis_store, job, config):
    """Submit a new job"""
    job.state = 'queued'
    limit = config['MAX_JOBS_PER_USER']
    vips = config['VIP_USERS']

    if job.email in vips:
        queue = config['PRIORITY_QUEUE']
    elif job.minimal:
        queue = config['FAST_QUEUE']
    else:
        if job.email and _count_pending_jobs_with_email(redis_store, job) > limit:
            _waitlist_job(redis_store, job, job.email)
            return
        elif _count_pending_jobs_with_ip(redis_store, job) > limit:
            _waitlist_job(redis_store, job, job.ip_addr)
            return

        if job.jobtype == app.config['LEGACY_JOBTYPE']:
            queue = config['LEGACY_QUEUE']
        else:
            queue = config['DEFAULT_QUEUE']

    if job.needs_download:
        queue = "{}:{}".format(queue, config['DOWNLOAD_QUEUE_SUFFIX'])
    _add_to_queue(redis_store, queue, job)


def _dark_launch_job(redis_store, job, config):
    """Submit a copy of the job to the development queue so we can test new versions on real data"""

    percentage = config['DARK_LAUNCH_PERCENTAGE']
    rand = random.randrange(0, 100)
    if rand >= percentage:
        return

    new_job_id = _generate_jobid(config['TAXON'])
    new_job = Job.fromExisting(new_job_id, job)
    new_job.email = config['DARK_LAUNCH_EMAIL']
    new_job.jobtype = 'antismash5'

    _copy_files(config['RESULTS_PATH'], job, new_job)

    queue = config['DEVELOPMENT_QUEUE']
    if new_job.needs_download:
        queue = "{}:{}".format(queue, config['DOWNLOAD_QUEUE_SUFFIX'])
    _add_to_queue(redis_store, queue, new_job)


def _copy_files(basedir, old_job, new_job):
    """When duplicating a job, copy over available input files"""

    old_dirname = path.join(basedir, old_job.job_id, 'input')
    new_dirname = path.join(basedir, new_job.job_id, 'input')

    os.makedirs(new_dirname, exist_ok=True)

    if old_job.filename:
        old_filename = path.join(old_dirname, old_job.filename)
        new_filename = path.join(new_dirname, new_job.filename)
        shutil.copyfile(old_filename, new_filename)

    if old_job.gff3:
        old_filename = path.join(old_dirname, old_job.gff3)
        new_filename = path.join(new_dirname, new_job.gff3)
        shutil.copyfile(old_filename, new_filename)


def _count_pending_jobs_with_email(redis_store, job):
    """Count how many jobs are pending for the email of the current job"""
    count = 0
    for job_id in redis_store.lrange(app.config['DEFAULT_QUEUE'], 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'email') == job.email:
            count += 1
    for job_id in redis_store.lrange(app.config['LEGACY_QUEUE'], 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'email') == job.email:
            count += 1

    return count


def _count_pending_jobs_with_ip(redis_store, job):
    """Count how many jobs are pending for the IP address of the current job"""
    count = 0
    for job_id in redis_store.lrange(app.config['DEFAULT_QUEUE'], 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'ip_addr') == job.ip_addr:
            count += 1
    for job_id in redis_store.lrange(app.config['LEGACY_QUEUE'], 0, -1):
        job_key = "job:{}".format(job_id)
        if redis_store.hget(job_key, 'ip_addr') == job.ip_addr:
            count += 1

    return count


def _waitlist_job(redis_store, job, attribute):
    """Put the given job on a waitlist"""
    job.state = 'waiting'
    job.status = 'waiting: Too many jobs in queue for this user.'
    waitlist = '{}:{}'.format(app.config['WAITLIST_PREFIX'], attribute)
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

    job.jobtype = request.form.get('jobtype', 'antismash4')

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

    dirname = path.join(app.config['RESULTS_PATH'], job.job_id, 'input')
    os.makedirs(dirname)

    if ncbi != '':
        if ' ' in ncbi:
            raise BadRequest("Spaces are not allowed in an NCBI ID.")
        job.download = ncbi
        job.needs_download = True
    else:
        upload = request.files['seq']

        if upload is not None:
            filename = secure_filename(upload.filename)
            upload.save(path.join(dirname, filename))
            if not path.exists(path.join(dirname, filename)):
                raise BadRequest("Could not save file!")
            job.filename = filename
            job.needs_download = False
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

    _submit_job(redis_store, job, app.config)
    _dark_launch_job(redis_store, job, app.config)
    return job


def secure_filename(name):
    """Even more secure filenames"""
    secure_name = werkzeug.utils.secure_filename(name)
    secure_name = secure_name.lstrip('-')
    return secure_name
