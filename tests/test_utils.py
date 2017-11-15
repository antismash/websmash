#!/usr/bin/env python
"""Tests for utility functions"""
from minimock import TraceTracker, assert_same_trace
from websmash import get_db, utils
from websmash.models import Job


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

    job = Job()

    utils._submit_job(fake_db, job, 5, {})

    assert old_len + 1 == fake_db.llen('jobs:queued')


def test_secure_filename():
    """Test generated filename is secure (enough)"""
    expected = "etc_passwd"
    bad_name = "../../../etc/passwd"
    assert utils.secure_filename(bad_name) == expected

    bad_name = "-etc_passwd"
    assert utils.secure_filename(bad_name) == expected
