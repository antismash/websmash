#!/usr/bin/env python
"""Utility functions for websmash"""
import os
import shutil

from flask import request
from os import path
import platform
import random
import uuid

import werkzeug.utils
from antismash_models import SyncJob as Job

from websmash import app, get_db, DataStore
from websmash.error_handlers import BadRequest


def generate_confirmation_mail(message):
    """Generate confirmation email message from template"""
    confirmation_template = """We have received your feedback to antiSMASH and will reply to you as soon as possible.
Your message was:

%s
"""
    return confirmation_template % message


def _generate_jobid(taxon: str) -> str:
    """Generate a job uid based on the taxon"""
    return "{}-{}".format(taxon, uuid.uuid4())


def _add_to_queue(redis_store, job):
    """Add job to a specified job queue"""
    queue = job.target_queues.pop()
    job.commit()
    redis_store.lpush(queue, job.job_id)


def _submit_job(redis_store, job, config):
    """Submit a new job"""
    job.state = 'queued'
    limit = config['MAX_JOBS_PER_USER']
    vips = config['VIP_USERS']

    if job.email in vips:
        job.target_queues.append(config['PRIORITY_QUEUE'])
    elif job.minimal:
        job.target_queues.append(config['FAST_QUEUE'])
    else:
        if app.config['LEGACY_JOBTYPE'] != app.config['DEFAULT_JOBTYPE'] and \
           job.jobtype == app.config['LEGACY_JOBTYPE']:
            job.target_queues.append(config['LEGACY_QUEUE'])
        else:
            job.target_queues.append(config['DEFAULT_QUEUE'])

        if job.email and _count_pending_jobs_with_email(redis_store, job) > limit:
            _waitlist_job(job, job.email)
        elif _count_pending_jobs_with_ip(redis_store, job) > limit:
            _waitlist_job(job, job.ip_addr)

    if job.needs_download:
        job.target_queues.append(config['DOWNLOAD_QUEUE'])
    _add_to_queue(redis_store, job)


def _dark_launch_job(redis_store, job, config):
    """Submit a copy of the job to the development queue so we can test new versions on real data"""

    if not _want_to_run(config['DARK_LAUNCH_PERCENTAGE']):
        return

    new_job_id = _generate_jobid(config['TAXON'])
    new_job = Job.fromExisting(new_job_id, job)
    new_job.email = config['DARK_LAUNCH_EMAIL']
    new_job.jobtype = config['DARK_LAUNCH_JOBTYPE']

    # Activate all the extra analyses so we can test those as well
    new_job.asf = True
    new_job.clusterhmmer = True
    new_job.pfam2go = True
    new_job.rre = True
    new_job.tigrfam = True
    new_job.tfbs = True

    # Activate all the *clusterblast options
    new_job.clusterblast = True
    new_job.knownclusterblast = True
    new_job.subclusterblast = True

    new_job.cc_mibig = True

    # Don't always run smcog-trees
    if _want_to_run(config['RARE_TEST_PERCENTAGE']):
        new_job.smcog_trees = True

    # Only run cassis occasionally, and only on fungal jobs
    if job.taxon == "fungi" and _want_to_run(config['RARE_TEST_PERCENTAGE']):
        new_job.cassis = True

    _copy_files(config['RESULTS_PATH'], job, new_job)

    new_job.target_queues = [config['DEVELOPMENT_QUEUE']]

    if new_job.needs_download:
        new_job.target_queues.append(config['DOWNLOAD_QUEUE'])

    _add_to_queue(redis_store, new_job)


def _want_to_run(percentage: int) -> bool:
    """Check if a random number 0-100 is below percentage"""
    rand = random.randrange(0, 100)
    return rand < percentage


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

    if old_job.sideload:
        old_filename = path.join(old_dirname, old_job.sideload)
        new_filename = path.join(new_dirname, new_job.sideload)
        shutil.copyfile(old_filename, new_filename)


def _count_pending_jobs_with_email(redis_store: DataStore, job: Job) -> int:
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


def _count_pending_jobs_with_ip(redis_store: DataStore, job: Job) -> int:
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


def _waitlist_job(job, attribute):
    """Put the given job on a waitlist"""
    job.state = 'waiting'
    job.status = 'waiting: Too many jobs in queue for this user.'
    waitlist = '{}:{}'.format(app.config['WAITLIST_PREFIX'], attribute)
    job.target_queues.append(waitlist)


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
    job.cc_mibig = _get_checkbox(request, 'cc_mibig')

    job.jobtype = request.form.get('jobtype', app.config['DEFAULT_JOBTYPE'])
    if job.jobtype not in (app.config['LEGACY_JOBTYPE'], app.config['DEFAULT_JOBTYPE']):
        raise BadRequest(f"Invalid jobtype {job.jobtype}")

    genefinder = request.form.get('genefinder', '')
    if genefinder:
        job.genefinder = genefinder

    hmmdetection_strictness = request.form.get('hmmdetection_strictness', '')
    if hmmdetection_strictness:
        job.hmmdetection_strictness = hmmdetection_strictness

    val = request.form.get('from', 0, type=int)
    if val:
        job.from_pos = val

    val = request.form.get('to', 0, type=int)
    if val:
        job.to_pos = val

    job.asf = _get_checkbox(request, 'asf')
    job.tta = _get_checkbox(request, 'tta')
    job.cassis = _get_checkbox(request, 'cassis')
    job.clusterhmmer = _get_checkbox(request, 'clusterhmmer')
    job.pfam2go = _get_checkbox(request, 'pfam2go')
    job.rre = _get_checkbox(request, 'rre')
    job.tigrfam = _get_checkbox(request, 'tigrfam')
    job.tfbs = _get_checkbox(request, "tfbs")

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

    if 'sideload' in request.files:
        sideload = request.files['sideload']
        if sideload is not None:
            sideload_filename = secure_filename(sideload.filename)
            sideload.save(path.join(dirname, sideload_filename))
            if not path.exists(path.join(dirname, sideload_filename)):
                raise BadRequest("Could not save sideload info file!")
            job.sideload = sideload_filename

    job.trace.append("{}-api".format(platform.node()))

    _submit_job(redis_store, job, app.config)
    _dark_launch_job(redis_store, job, app.config)
    return job


def secure_filename(name: str) -> str:
    """Even more secure filenames"""
    secure_name = werkzeug.utils.secure_filename(name)
    secure_name = secure_name.lstrip('-')
    return secure_name
