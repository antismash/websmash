import uuid


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
