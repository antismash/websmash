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

    utils._submit_job(fake_db, job, 5, {})

    assert old_len + 1 == fake_db.llen('jobs:queued')


def test_secure_filename():
    """Test generated filename is secure (enough)"""
    expected = "etc_passwd"
    bad_name = "../../../etc/passwd"
    assert utils.secure_filename(bad_name) == expected

    bad_name = "-etc_passwd"
    assert utils.secure_filename(bad_name) == expected


def test__dark_launch_job(app, mocker):
    fake_db = get_db()
    assert app.config['FAKE_DB']
    fake_randrange = mocker.patch('random.randrange', return_value=15)
    old_len = fake_db.llen('jobs:development')

    job = Job(fake_db, 'taxon-fake')
    utils._dark_launch_job(fake_db, job, app.config)
    assert fake_db.llen('jobs:development') == old_len
    fake_randrange.assert_called_once_with(0, 100)

    fake_randrange = mocker.patch('random.randrange', return_value=5)
    utils._dark_launch_job(fake_db, job, app.config)
    assert fake_db.llen('jobs:development') == old_len + 1
    fake_randrange.assert_called_once_with(0, 100)


def test__copy_files(app, mocker):
    fake_db = get_db()
    assert app.config['FAKE_DB']
    old_job = Job(fake_db, 'bacteria-old')
    old_job.filename = 'fake.fa'
    old_job.gff3 = 'fake.gff'
    new_job = Job.fromExisting('bacteria-new', old_job)

    fake_makedirs = mocker.patch('os.makedirs')
    fake_chmod = mocker.patch('os.chmod')
    fake_copyfile = mocker.patch('shutil.copyfile')

    utils._copy_files('fake_base', old_job, new_job)

    new_job_basedir = os.path.join('fake_base', new_job.job_id)

    fake_makedirs.assert_called_once_with(new_job_basedir, exist_ok=True)
    fake_chmod.assert_called_once_with(new_job_basedir, 0o775)
    old_filename = os.path.join('fake_base', old_job.job_id, old_job.filename)
    old_gff3 = os.path.join('fake_base', old_job.job_id, old_job.gff3)
    new_filename = os.path.join('fake_base', new_job.job_id, new_job.filename)
    new_gff3 = os.path.join('fake_base', new_job.job_id, new_job.gff3)
    fake_copyfile.assert_has_calls([call(old_filename, new_filename), call(old_gff3, new_gff3)])
