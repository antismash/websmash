from flask.ext.testing import TestCase
import websmash
from websmash.models import Job, Notice
from tests.test_shared import ModelTestCase

class JobTestCase(ModelTestCase):
    def test_job_instantiate(self):
        """Test if job can be instantiated"""
        job = Job()
        assert job is not None

    def test_job_unique_uid(self):
        """Test if two different job objects get different uids"""
        first = Job()
        second = Job()
        assert first.uid != second.uid

    def test_job_repr(self):
        """Test that the repr matches the job data"""
        job = Job()
        assert job.uid in str(job)
        assert job.status in str(job)

    def test_job_get_status(self):
        """Test that Job.get_status() is sane"""
        job = Job()
        assert job.get_status() == 'pending'
        assert job.status == job.get_status()
        job = Job(status='funky')
        assert job.get_status() == 'funky'

    def test_job_get_short_status(self):
        """Test that Job.get_short_status() is sane"""
        job = Job(status='pending: Waiting for Godot')
        assert job.get_short_status() == 'pending'

    def test_job_email(self):
        """Test that Job.email returns the correct value"""
        job = Job(email="ex@mp.le")
        assert job.email == "ex@mp.le"

    def test_job_jobtype_default(self):
        """Test that Job.jobtype is 'antismash' if not specified"""
        job = Job()
        assert job.jobtype == "antismash"

class NoticeTestCase(ModelTestCase):
    def test_notice_instantiate(self):
        "Test if Notice can be instantiated"
        notice = Notice(u'test teaser', u'test text')
        assert notice

    def test_notice_repr(self):
        "Test if Notice repr matches the data"
        notice = Notice(u'test teaser', u'test text')
        assert notice.teaser in str(notice)
        assert notice.category in str(notice)

    def test_json(self):
        "Test if Notice json property matches the data"
        notice = Notice(u'test teaser', u'test text')
        d = notice.json
        fmt = "%Y-%m-%d %H:%M:%S"
        self.assertEquals(d['category'], notice.category)
        self.assertEquals(d['teaser'], notice.teaser)
        self.assertEquals(d['text'], notice.text)
        self.assertEquals(d['added'], notice.added.strftime(fmt))
        self.assertEquals(d['show_from'], notice.show_from.strftime(fmt))
        self.assertEquals(d['show_until'], notice.show_until.strftime(fmt))
