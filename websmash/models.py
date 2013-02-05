import uuid
from datetime import datetime, timedelta
from websmash import db

class Job(db.Model):
    __tablename__ = 'jobs'
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
    from_pos = db.Column(db.Integer)
    to_pos = db.Column(db.Integer)
    molecule = db.Column(db.String(4))
    inclusive = db.Column(db.Boolean)
    smcogs = db.Column(db.Boolean)
    clusterblast = db.Column(db.Boolean)
    subclusterblast = db.Column(db.Boolean)
    fullblast = db.Column(db.Boolean)
    fullhmm = db.Column(db.Boolean)
    download = db.Column(db.Boolean)
    status = db.Column(db.String(500))

    def __init__(self, **kwargs):
        self.uid = unicode(uuid.uuid4())
        self.jobtype = kwargs.get('jobtype', 'antismash')
        self.email = kwargs.get('email', '')
        self.filename = kwargs.get('filename', '')
        self.added = kwargs.get('added', datetime.utcnow())
        self.last_changed = self.added
        self.geneclustertypes = kwargs.get('geneclustertypes', '1')
        self.taxon = kwargs.get('taxon', 'p')
        self.gtransl = kwargs.get('gtransl', 1)
        self.minglength = kwargs.get('minglength', 50)
        self.genomeconf = kwargs.get('genomeconf', 'l')
        self.from_pos = kwargs.get('from', '0')
        self.to_pos = kwargs.get('to', '0')
        self.molecule = kwargs.get('molecule', 'nucl')
        self.inclusive = kwargs.get('inclusive', False)
        self.smcogs = kwargs.get('smcogs', False)
        self.clusterblast = kwargs.get('clusterblast', False)
        self.subclusterblast = kwargs.get('subclusterblast', False)
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

class Notice(db.Model):
    __tablename__ = 'notices'
    id         = db.Column(db.String(36), primary_key=True)
    added      = db.Column(db.DateTime)
    show_from  = db.Column(db.DateTime)
    show_until = db.Column(db.DateTime)
    category   = db.Column(db.String(100))
    teaser     = db.Column(db.String(500))
    text       = db.Column(db.String(2000))

    def __init__(self,
                 teaser,
                 text,
                 added=None,
                 show_from=None,
                 show_until=None,
                 category=u'notice'
                ):
        self.id = unicode(uuid.uuid4())
        self.added = added and added or datetime.utcnow()
        self.show_from = show_from and show_from or datetime.utcnow()
        self.show_until = show_until and show_until or \
                            datetime.utcnow() + timedelta(weeks=1)
        self.category = category
        self.teaser = teaser
        self.text = text

    def __repr__(self):
        return '<Notice (%s): %r>' % (self.category, self.teaser)

    @property
    def json(self):
        # first get rid of all internal attributes
        d = self.__dict__
        ret = dict((key, d[key]) for key in d.keys() if not key.startswith('_'))

        # replace datetime objects by a timestring
        for key in ret.keys():
            if hasattr(ret[key], 'strftime'):
                ret[key] = ret[key].strftime('%Y-%m-%d %H:%M:%S')

        return ret

class Stat(db.Model):
    __tablename__ = 'stats'
    uid      = db.Column('uid', db.String(128), primary_key=True)
    jobtype  = db.Column('jobtype', db.String(20))
    added    = db.Column('added', db.DateTime)
    finished = db.Column('finished', db.DateTime)

    def __init__(self,
                 uid,
                 jobtype="antismash",
                 added=None,
                 finished=None,
                ):
        self.uid = uid
        self.added = added if added else datetime.utcnow()
        self.finished = finished if finished else datetime.utcnow()

    def __repr__(self):
        return '<Stat (%s): %s - %s>' % (self.uid, self.added, self.finished)
