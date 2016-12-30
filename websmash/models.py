import uuid
from datetime import datetime, timedelta


def get_bool(obj, param, default=False):
    # type: (dict, str, bool) -> bool
    """convert Redis' string serialised boolean values back to true booleans"""
    val = obj.get(param, default)
    if isinstance(val, basestring):
        val = (val.lower() == 'true')
    return val

def _generate_jobid(taxon):
    """Generate a job uid based on the taxon"""
    return "{}-{}".format(taxon, uuid.uuid4())


class Job(object):
    def __init__(self, **kwargs):
        self.taxon = kwargs.get('taxon', 'bacteria')
        self.uid = kwargs.get('uid', _generate_jobid(self.taxon))
        self.jobtype = kwargs.get('jobtype', 'antismash4')
        self.email = kwargs.get('email', '')
        self.filename = kwargs.get('filename', '')
        added = kwargs.get('added', datetime.utcnow())
        if isinstance(added, (str, unicode)):
            self.added = datetime.strptime(added, "%Y-%m-%d %H:%M:%S.%f")
        else:
            self.added = added
        last_changed = kwargs.get('last_changed', self.added)
        if isinstance(last_changed, (str, unicode)):
            self.last_changed = datetime.strptime(last_changed, "%Y-%m-%d %H:%M:%S.%f")
        else:
            self.last_changed = last_changed
        self.geneclustertypes = kwargs.get('geneclustertypes', '1')
        self.genefinder = kwargs.get('genefinder', 'prodigal')
        self.gtransl = kwargs.get('gtransl', 1)
        self.minglength = kwargs.get('minglength', 50)
        self.genomeconf = kwargs.get('genomeconf', 'l')
        self.all_orfs = get_bool(kwargs, 'all_orfs', False)
        self.from_pos = int(kwargs.get('from', kwargs.get('from_pos', 0)))
        self.to_pos = int(kwargs.get('to', kwargs.get('to_pos', 0)))
        self.molecule = kwargs.get('molecule', 'nucl')
        self.inclusive = get_bool(kwargs, 'inclusive', False)
        self.cf_cdsnr = int(kwargs.get('cf_cdsnr', 5))
        self.cf_npfams = int(kwargs.get('cf_npfams', 5))
        self.cf_threshold = float(kwargs.get('cf_threshold', 0.6))
        self.smcogs = get_bool(kwargs, 'smcogs', False)
        self.clusterblast = get_bool(kwargs, 'clusterblast', False)
        self.knownclusterblast = get_bool(kwargs, 'knownclusterblast', False)
        self.subclusterblast = get_bool(kwargs, 'subclusterblast', False)
        self.fullhmmer = get_bool(kwargs, 'fullhmmer', False)
        self.asf = get_bool(kwargs, 'asf', False)
        self.tta = get_bool(kwargs, 'tta', False)
        self.status = kwargs.get('status', 'pending')
        self.dispatcher = kwargs.get('dispatcher', 'unknown')
        self.download = kwargs.get('download', '')

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
