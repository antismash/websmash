# -*- coding: utf-8 -*-
from websmash.models import Job, Notice
from tests.test_shared import WebsmashTestCase


class AjaxTestCase(WebsmashTestCase):
    def setUp(self):
        super(AjaxTestCase, self).setUp()
        self.app.config['OLD_JOB_COUNT'] = 89132

    def test_server_status(self):
        """Test if server status returns the correct values"""
        expected_status = dict(
            status='idle',
            queue_length=0,
            running=0,
            long_running=0,
            total_jobs=89132,
            ts_queued=None,
            ts_queued_m=None,
            ts_timeconsuming=None,
            ts_timeconsuming_m=None
        )
        rv = self.client.get('/server_status')
        self.assertEquals(rv.json, expected_status)

        # fake a normal job
        j = Job()
        redis_store = self._ctx.g._database
        redis_store.hmset(u'job:%s' % j.uid, j.get_dict())
        redis_store.lpush('jobs:queued', j.uid)
        rv = self.client.get('/server_status')
        expected_status = dict(
            status='working',
            queue_length=1,
            running=0,
            long_running=0,
            total_jobs=89132,
            ts_queued=j.added.strftime("%Y-%m-%d %H:%M"),
            ts_queued_m=j.added.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ts_timeconsuming=None,
            ts_timeconsuming_m=None
        )
        self.assertEquals(rv.json, expected_status)

        # fake a timeconsuming job
        redis_store.rpoplpush('jobs:queued', 'jobs:timeconsuming')
        rv = self.client.get('/server_status')
        expected_status = dict(
            status='working',
            queue_length=0,
            running=0,
            long_running=1,
            total_jobs=89132,
            ts_queued=None,
            ts_queued_m=None,
            ts_timeconsuming=j.added.strftime("%Y-%m-%d %H:%M"),
            ts_timeconsuming_m=j.added.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        self.assertEquals(rv.json, expected_status)

        # fake a running job
        j.status="running: not really"
        redis_store.rpoplpush('jobs:timeconsuming', 'jobs:running')
        rv = self.client.get('/server_status')
        expected_status = dict(
            status='working',
            queue_length=0,
            running=1,
            long_running=0,
            total_jobs=89132,
            ts_queued=None,
            ts_queued_m=None,
            ts_timeconsuming=None,
            ts_timeconsuming_m=None
        )
        self.assertEquals(rv.json, expected_status)


    def test_current_notices(self):
        "Test if current notices are displayed"
        rv = self.client.get('/current_notices')
        self.assertEquals(rv.json, dict(notices=[]))
        n = Notice(u'Teaser', u'Text')
        redis_store = self._ctx.g._database
        redis_store.hmset(u'notice:%s' % n.id, n.json)
        rv = self.client.get('/current_notices')
        self.assertEquals(rv.json, dict(notices=[n.json]))
