import uuid
from datetime import datetime, timedelta

class Job(object):
    def __init__(self, **kwargs):
        self.uid = kwargs.get('uid', unicode(uuid.uuid4()))
        self.jobtype = kwargs.get('jobtype', 'antismash')
        self.email = kwargs.get('email', '')
        self.filename = kwargs.get('filename', '')
        added = kwargs.get('added', datetime.utcnow())
        if isinstance(added, (str, unicode)):
            self.added = datetime.strptime(added, "%Y-%m-%d %H:%M:%S.%f")
        else:
            self.added = added
        self.last_changed = self.added
        self.geneclustertypes = kwargs.get('geneclustertypes', '1')
        self.taxon = 'e' if kwargs.get('eukaryotic', False) else 'p'
        self.gtransl = kwargs.get('gtransl', 1)
        self.minglength = kwargs.get('minglength', 50)
        self.genomeconf = kwargs.get('genomeconf', 'l')
        self.all_orfs = kwargs.get('all_orfs', True)
        self.from_pos = int(kwargs.get('from', kwargs.get('from_pos', 0)))
        self.to_pos = int(kwargs.get('to', kwargs.get('to_pos', 0)))
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

    def get_dict(self):
        return self.__dict__

    def __repr__(self):
        return '<Job %r (%s)>' % (self.uid, self.status)

class Notice(object):
    def __init__(self,
                 teaser,
                 text,
                 added=None,
                 show_from=None,
                 show_until=None,
                 category=u'notice',
                 id=None
                ):
        self.id = id if id is not None else unicode(uuid.uuid4())
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

class Stat(object):
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
