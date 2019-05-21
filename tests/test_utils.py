#!/usr/bin/env python
"""Tests for utility functions"""

from antismash_models import SyncJob as Job
from minimock import TraceTracker, assert_same_trace
import os
from unittest.mock import call

from websmash import get_db, utils


def test_generate_confirmation_mail():
    """Test generation of a confirmation email"""
    # abuse the TraceTracker to make use of doctest features
    tt = TraceTracker()
    mail = utils.generate_confirmation_mail(message="Test!")

    tt.out.write(mail)

    expected = """We have received your feedback to antiSMASH and will reply to you as soon as possible.
Your message was:
<BLANKLINE>
Test!
"""

    assert_same_trace(tt, expected)


def test__get_checkbox():
    """Test getting a boolean value from a form checkbox"""
    class FakeRequest(object):
        def __init__(self):
            self.form = dict()

    fake_req = FakeRequest()
    fake_req.form['enabled'] = u'on'
    fake_req.form['disabled'] = u'off'
    fake_req.form['also_enabled'] = u'true'
    fake_req.form['also_disabled'] = u'false'

    assert utils._get_checkbox(fake_req, 'enabled')
    assert not utils._get_checkbox(fake_req, 'disabled')
    assert utils._get_checkbox(fake_req, 'also_enabled')
    assert not utils._get_checkbox(fake_req, 'also_disabled')


def test__submit_job(app):
    """Test job submission works as expected"""
    fake_db = get_db()
    assert app.config['FAKE_DB']
    old_len = fake_db.llen('jobs:queued')

    job = Job(fake_db, 'taxon-fake')

    utils._submit_job(fake_db, job, app.config)

    assert old_len + 1 == fake_db.llen('jobs:queued')


def test__submit_job_vip(app):
    """Test VIP job submission works as expected"""
    fake_db = get_db()
    queue = app.config['PRIORITY_QUEUE']
    assert app.config['FAKE_DB']
    old_len = fake_db.llen(queue)
    app.config['VIP_USERS'].add('alice@example.org')

    # No priority queue for Bob
    job = Job(fake_db, 'taxon-fake')
    job.email = 'bob@example.org'
    job.commit()
    utils._submit_job(fake_db, job, app.config)
    assert old_len == fake_db.llen(queue)

    # Priority queue for Alice
    job = Job(fake_db, 'taxon-fake')
    job.email = 'alice@example.org'
    job.commit()
    utils._submit_job(fake_db, job, app.config)
    assert old_len + 1 == fake_db.llen(queue)

    # Priority queue when downloading
    fake_db.ltrim(app.config['DOWNLOAD_QUEUE'], 2, 1)  # clear queue
    job = Job(fake_db, 'taxon-fake')
    job.email = 'alice@example.org'
    job.needs_download = True
    job.commit()
    utils._submit_job(fake_db, job, app.config)
    assert 1 == fake_db.llen(app.config['DOWNLOAD_QUEUE'])
    job.fetch()
    assert job.target_queues == [queue]


def test__submit_job_minimal(app):
    """Test fast mode job submission works as expected"""
    fake_db = get_db()
    queue = app.config['FAST_QUEUE']
    assert app.config['FAKE_DB']
    old_len = fake_db.llen(queue)

    job = Job(fake_db, 'taxon-fake')
    job.minimal = True
    job.commit()

    utils._submit_job(fake_db, job, app.config)

    assert old_len + 1 == fake_db.llen(queue)

    fake_db.ltrim(app.config['DOWNLOAD_QUEUE'], 2, 1)  # clear queue
    job = Job(fake_db, 'taxon-fake')
    job.minimal = True
    job.needs_download = True
    job.commit()

    utils._submit_job(fake_db, job, app.config)
    assert 1 == fake_db.llen(app.config['DOWNLOAD_QUEUE'])
    job.fetch()
    assert job.target_queues == [queue]


def test__submit_job_legacy(app):
    """Test legacy job submission works as expected"""
    fake_db = get_db()
    queue = app.config['LEGACY_QUEUE']
    legacy_jobtype = app.config['LEGACY_JOBTYPE']
    assert app.config['FAKE_DB']
    old_len = fake_db.llen(queue)

    job = Job(fake_db, 'taxon-fake')
    job.jobtype = legacy_jobtype
    job.commit()

    utils._submit_job(fake_db, job, app.config)

    assert old_len + 1 == fake_db.llen(queue)

    fake_db.ltrim(app.config['DOWNLOAD_QUEUE'], 2, 1)  # clear queue
    job = Job(fake_db, 'taxon-fake')
    job.jobtype = legacy_jobtype
    job.needs_download = True
    job.commit()

    utils._submit_job(fake_db, job, app.config)
    assert 1 == fake_db.llen(app.config['DOWNLOAD_QUEUE'])
    job.fetch()
    assert job.target_queues == [queue]


def test__submit_job_email_waitlist(app):
    """Test job submission waitlisting by email works as expected"""
    fake_db = get_db()
    email = "charles@example.com"
    queue = "{}:{}".format(app.config['WAITLIST_PREFIX'], email)
    assert app.config['FAKE_DB']
    app.config['MAX_JOBS_PER_USER'] = -1

    job = Job(fake_db, 'taxon-fake')
    job.email = email
    job.commit()

    utils._submit_job(fake_db, job, app.config)

    assert 1 == fake_db.llen(queue)

    fake_db.ltrim(app.config['DOWNLOAD_QUEUE'], 2, 1)  # clear queue
    job = Job(fake_db, 'taxon-fake')
    job.email = email
    job.needs_download = True
    job.commit()

    utils._submit_job(fake_db, job, app.config)
    assert 1 == fake_db.llen(app.config['DOWNLOAD_QUEUE'])
    job.fetch()
    assert job.target_queues == [app.config['DEFAULT_QUEUE'], queue]


def test__submit_job_ip_waitlist(app):
    """Test job submission waitlisting by IP works as expected"""
    fake_db = get_db()
    ip = "192.168.0.1"
    queue = "{}:{}".format(app.config['WAITLIST_PREFIX'], ip)
    assert app.config['FAKE_DB']
    app.config['MAX_JOBS_PER_USER'] = -1

    job = Job(fake_db, 'taxon-fake')
    job.ip_addr = ip
    job.commit()

    utils._submit_job(fake_db, job, app.config)

    assert 1 == fake_db.llen(queue)

    fake_db.ltrim(app.config['DOWNLOAD_QUEUE'], 2, 1)  # clear queue
    job = Job(fake_db, 'taxon-fake')
    job.ip_addr = ip
    job.needs_download = True
    job.commit()

    utils._submit_job(fake_db, job, app.config)
    assert 1 == fake_db.llen(app.config['DOWNLOAD_QUEUE'])
    job.fetch()
    assert job.target_queues == [app.config['DEFAULT_QUEUE'], queue]


def test_secure_filename():
    """Test generated filename is secure (enough)"""
    expected = "etc_passwd"
    bad_name = "../../../etc/passwd"
    assert utils.secure_filename(bad_name) == expected

    bad_name = "-etc_passwd"
    assert utils.secure_filename(bad_name) == expected

    bad_name = "LOCUS_05150 SusC/RagA family TonB-linked outer membrane protein.fasta"
    assert utils.secure_filename(bad_name) == "LOCUS_05150_SusC_RagA_family_TonB-linked_outer_membrane_protein.fasta"


def test__dark_launch_job(app, mocker):
    fake_db = get_db()
    assert app.config['FAKE_DB']
    app.config['DARK_LAUNCH_PERCENTAGE'] = 10
    fake_randrange = mocker.patch('random.randrange', return_value=15)
    old_len = fake_db.llen('jobs:development')

    job = Job(fake_db, 'taxon-fake')
    job.commit()
    utils._dark_launch_job(fake_db, job, app.config)
    assert fake_db.llen('jobs:development') == old_len
    fake_randrange.assert_called_once_with(0, 100)

    fake_randrange = mocker.patch('random.randrange', return_value=5)
    utils._dark_launch_job(fake_db, job, app.config)
    assert fake_db.llen('jobs:development') == old_len + 1
    fake_randrange.assert_called_once_with(0, 100)

    dark_job_id = fake_db.lrange('jobs:development', -1, -1)[0]
    dark_job = Job(fake_db, dark_job_id).fetch()
    assert dark_job.original_id == job.job_id

    # trim with start > end empties the list
    fake_db.ltrim('jobs:downloads', 2, 1)
    job.needs_download = True
    job.commit()
    utils._dark_launch_job(fake_db, job, app.config)
    assert fake_db.llen('jobs:downloads') == 1
    dark_job_id = fake_db.lrange('jobs:downloads', -1, -1)[0]
    dark_job = Job(fake_db, dark_job_id).fetch()
    assert dark_job.original_id == job.job_id
    assert dark_job.target_queues == ['jobs:development']


def test__copy_files(app, mocker):
    fake_db = get_db()
    assert app.config['FAKE_DB']
    old_job = Job(fake_db, 'bacteria-old')
    old_job.filename = 'fake.fa'
    old_job.gff3 = 'fake.gff'
    new_job = Job.fromExisting('bacteria-new', old_job)

    fake_makedirs = mocker.patch('os.makedirs')
    fake_copyfile = mocker.patch('shutil.copyfile')

    utils._copy_files('fake_base', old_job, new_job)

    new_job_basedir = os.path.join('fake_base', new_job.job_id, 'input')

    fake_makedirs.assert_called_once_with(new_job_basedir, exist_ok=True)
    old_filename = os.path.join('fake_base', old_job.job_id, 'input', old_job.filename)
    old_gff3 = os.path.join('fake_base', old_job.job_id, 'input', old_job.gff3)
    new_filename = os.path.join('fake_base', new_job.job_id, 'input', new_job.filename)
    new_gff3 = os.path.join('fake_base', new_job.job_id, 'input', new_job.gff3)
    fake_copyfile.assert_has_calls([call(old_filename, new_filename), call(old_gff3, new_gff3)])
