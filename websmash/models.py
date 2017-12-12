import uuid
from datetime import datetime, timedelta


def get_bool(obj, param, default=False):
    # type: (dict, str, bool) -> bool
    """convert Redis' string serialised boolean values back to true booleans"""
    val = obj.get(param, default)
    if isinstance(val, str):
        val = (val.lower() == 'true')
    return val

def _generate_jobid(taxon):
    """Generate a job uid based on the taxon"""
    return "{}-{}".format(taxon, uuid.uuid4())


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
        self.id = id if id is not None else str(uuid.uuid4())
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
