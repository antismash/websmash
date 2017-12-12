import uuid


def _generate_jobid(taxon):
    """Generate a job uid based on the taxon"""
    return "{}-{}".format(taxon, uuid.uuid4())
