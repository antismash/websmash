from flaskext.testing import TestCase
import websmash
from websmash.models import Job

class JobTestCase(TestCase):

    def create_app(self):
        app = websmash.app
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        websmash.mail.suppress = True
        return app

    def setUp(self):
        self.db = websmash.db
        self.db.create_all()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()

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
