#!/usr/bin/env python
"""Utility functions for websmash"""
import os

from flask import request
from os import path

import werkzeug.utils

from websmash import app, get_db
from websmash.models import Job
from websmash.error_handlers import BadRequest

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


def _submit_job(redis_store, job, limit, vips):
    """Submit a new job"""
    redis_store.hmset(u'job:%s' % job.uid, job.get_dict())
    if job.email in vips:
        redis_store.lpush(PRIORITY_QUEUE, job.uid)
    elif job.minimal:
        redis_store.lpush(FAST_QUEUE, job.uid)
    else:
        if job.email:
            if _count_pending_jobs_with_email(redis_store, job) > limit:
                _waitlist_job(redis_store, job, job.email)
                return
        elif _count_pending_jobs_with_ip(redis_store, job) > limit:
            _waitlist_job(redis_store, job, job.ip_addr)
            return

        redis_store.lpush(DEFAULT_QUEUE, job.uid)


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

    print "count is", count
    return count


def _waitlist_job(redis_store, job, attribute):
    """Put the given job on a waitlist"""
    print "waitlisting", job.uid, "based on", attribute
    redis_store.hset(u'job:%s' % job.uid, 'status', 'waiting: Too many jobs in queue for this user.')
    redis_store.lpush('{}:{}'.format(WAITLIST_PREFIX, attribute), job.uid)


def _get_checkbox(req, name):
    """Get True/False value for the checkbox of a given name"""
    str_value = req.form.get(name, u'off')
    return str_value == u'on' or str_value == 'true'


def dispatch_job():
    """Internal helper to dispatch a new job"""
    redis_store = get_db()
    taxon = app.config['TAXON']

    kwargs = dict(taxon=taxon)

    if 'X-Forwarded-For' in request.headers:
        kwargs['ip_addr'] = request.headers.getlist("X-Forwarded-For")[0].rpartition(' ')[-1]
    else:
        kwargs['ip_addr'] = request.remote_addr or 'untrackable'

    kwargs['ncbi'] = request.form.get('ncbi', '').strip()
    kwargs['email'] = request.form.get('email', '').strip()

    kwargs['minimal'] = _get_checkbox(request, 'minimal')

    kwargs['all_orfs'] = _get_checkbox(request, 'all_orfs')

    kwargs['smcogs'] = _get_checkbox(request, 'smcogs')

    kwargs['clusterblast'] = _get_checkbox(request, 'clusterblast')
    kwargs['knownclusterblast'] = _get_checkbox(request, 'knownclusterblast')
    kwargs['subclusterblast'] = _get_checkbox(request, 'subclusterblast')

    # We unfortunately are not 100% consistent in the API
    # so first try the deprecated 'full_hmmer', then possibly
    # overwrite with the new 'fullhmmer'
    kwargs['fullhmmer'] = _get_checkbox(request, 'full_hmmer')
    kwargs['fullhmmer'] = _get_checkbox(request, 'fullhmmer')

    kwargs['genefinder'] = request.form.get('genefinder', 'prodigal')
    kwargs['trans_table'] = request.form.get('trans_table', 1, type=int)
    kwargs['gene_length'] = request.form.get('gene_length', 50, type=int)

    kwargs['from_pos'] = request.form.get('from', 0, type=int)
    kwargs['to_pos'] = request.form.get('to', 0, type=int)

    kwargs['inclusive'] = _get_checkbox(request, 'inclusive')
    kwargs['cf_cdsnr'] = request.form.get('cf_cdsnr', 5, type=int)
    kwargs['cf_npfams'] = request.form.get('cf_npfams', 5, type=int)
    kwargs['cf_threshold'] = request.form.get('cf_threshold', 0.6, type=float)

    kwargs['borderpredict'] = _get_checkbox(request, 'borderpredict')

    kwargs['asf'] = _get_checkbox(request, 'asf')
    kwargs['tta'] = _get_checkbox(request, 'tta')
    kwargs['transatpks_da'] = _get_checkbox(request, 'transatpks_da')
    kwargs['cassis'] = _get_checkbox(request, 'cassis')

    # if 'legacy' checkbox is set but not in minimal mode, start an antismash3 job instead
    kwargs['jobtype'] = 'antismash4'
    if _get_checkbox(request, 'legacy') and not kwargs['minimal']:
        kwargs['jobtype'] = 'antismash3'

    job = Job(**kwargs)
    dirname = path.join(app.config['RESULTS_PATH'], job.uid)
    os.mkdir(dirname)

    if kwargs['ncbi'] != '':
        if ' ' in kwargs['ncbi']:
            raise BadRequest("Spaces are not allowed in an NCBI ID.")
        job.download = kwargs['ncbi']
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
