"""REST-like API for submitting and querying antiSMASH-style jobs"""

from flask import jsonify
from websmash import app, get_db
from websmash.models import Job


@app.route('/api/v1.0/version')
def get_version():
    """Return version information"""
    version_dict = {
        'api': '1.0.0',
        'antismash_generation': '4',
    }
    return jsonify(version_dict)


@app.route('/api/v1.0/stats')
def get_stats():
    redis_store = get_db()
    pending = redis_store.llen('jobs:queued')
    long_running = redis_store.llen("jobs:timeconsuming")
    running = redis_store.llen('jobs:running')

    # carry over jobs count from the old database from the config
    total_jobs = app.config['OLD_JOB_COUNT'] + redis_store.llen('jobs:completed') + \
        redis_store.llen('jobs:failed')

    if pending + long_running + running > 0:
        status = 'working'
    else:
        status = 'idle'

    ts_queued, ts_queued_m = _get_job_timestamps(_get_oldest_job("jobs:queued"))
    ts_timeconsuming, ts_timeconsuming_m = _get_job_timestamps(_get_oldest_job("jobs:timeconsuming"))

    return jsonify(status=status, queue_length=pending, running=running,
                   long_running=long_running, total_jobs=total_jobs,
                   ts_queued=ts_queued, ts_queued_m=ts_queued_m,
                   ts_timeconsuming=ts_timeconsuming, ts_timeconsuming_m=ts_timeconsuming_m)


def _get_oldest_job(queue):
    """Get the oldest job in a queue"""
    redis_store = get_db()
    try:
        res = redis_store.hgetall("job:%s" % redis_store.lrange(queue, -1, -1)[0])
    except IndexError:
        return None

    return Job(**res)


def _get_job_timestamps(job):
    """Get both a readable and a machine-readable timestamp for a job"""
    if job is None:
        return None, None
    return job.added.strftime("%Y-%m-%d %H:%M"), job.added.strftime("%Y-%m-%dT%H:%M:%SZ")


@app.route('/api/v1.0/news')
def get_news():
    """Display current notices"""
    redis_store = get_db()
    rets = redis_store.keys('notice:*')
    notices = [redis_store.hgetall(n) for n in rets]
    return jsonify(notices=notices)
