import uuid
from datetime import datetime
from websmash import db

class Job(db.Model):
    uid = db.Column(db.String(128), primary_key=True)
    jobtype = db.Column(db.String(20))
    email = db.Column(db.String(500))
    filename = db.Column(db.String(500))
    added = db.Column(db.DateTime)
    last_changed = db.Column(db.DateTime)
    geneclustertypes = db.Column(db.String(128))
    taxon = db.Column(db.String(1))
    gtransl = db.Column(db.Integer)
    minglength = db.Column(db.Integer)
    genomeconf = db.Column(db.String(20))
    smcogs = db.Column(db.Boolean)
    clusterblast = db.Column(db.Boolean)
    fullblast = db.Column(db.Boolean)
    fullhmm = db.Column(db.Boolean)
    download = db.Column(db.Boolean)
    status = db.Column(db.String(500))

    def __init__(self, **kwargs):
        self.uid = unicode(uuid.uuid4())
        self.jobtype = kwargs.get('jobtype', 'antismash')
        self.jobtype = kwargs.get('email', '')
        self.filename = kwargs.get('filename', '')
        self.added = kwargs.get('added', datetime.utcnow())
        self.last_changed = self.added
        self.geneclustertypes = kwargs.get('geneclustertypes', '1')
        self.taxon = kwargs.get('taxon', 'e')
        self.gtransl = kwargs.get('gtransl', 1)
        self.minglength = kwargs.get('minglength', 50)
        self.genomeconf = kwargs.get('genomeconf', 'l')
        self.smcogs = kwargs.get('smcogs', False)
        self.clusterblast = kwargs.get('clusterblast', False)
        self.fullblast = kwargs.get('fullblast', False)
        self.fullhmm = kwargs.get('fullhmm', False)
        self.download = kwargs.get('download', False)
        self.status = kwargs.get('status', 'pending')

    def get_short_status(self):
        """Get a short status description useful for icon names"""
        return self.status.split(':')[0]

    def get_status(self):
        return self.status

    def __repr__(self):
        return '<Job %r (%s)>' % (self.uid, self.status)


