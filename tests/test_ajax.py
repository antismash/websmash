# -*- coding: utf-8 -*-
from antismash_models import SyncJob as Job
from websmash.models import Notice
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
            fast=0,
            total_jobs=89132,
            ts_queued=None,
            ts_queued_m=None,
            ts_fast=None,
            ts_fast_m=None,
        )
        rv = self.client.get('/api/v1.0/stats')
        self.assertEquals(rv.json, expected_status)

        # fake a fast job
        redis_store = self._ctx.g._database
        fake_id = 'taxon-fake'
        j = Job(redis_store, fake_id)
        j.commit()
        redis_store.lpush('jobs:minimal', j.job_id)
        rv = self.client.get('/api/v1.0/stats')
        expected_status = dict(
            status='working',
            queue_length=0,
            running=0,
            fast=1,
            total_jobs=89132,
            ts_fast=j.added.strftime("%Y-%m-%d %H:%M"),
            ts_fast_m=j.added.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ts_queued=None,
            ts_queued_m=None,
        )
        self.assertEquals(rv.json, expected_status)

        # fake a normal job
        redis_store.lpop('jobs:minimal')
        redis_store.lpush('jobs:queued', j.job_id)
        rv = self.client.get('/api/v1.0/stats')
        expected_status = dict(
            status='working',
            queue_length=1,
            running=0,
            fast=0,
            total_jobs=89132,
            ts_queued=j.added.strftime("%Y-%m-%d %H:%M"),
            ts_queued_m=j.added.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ts_fast=None,
            ts_fast_m=None,
        )
        self.assertEquals(rv.json, expected_status)

        # fake a running job
        j.state = "running"
        j.status = "running: not really"
        j.commit()
        redis_store.rpoplpush('jobs:queued', 'jobs:running')
        rv = self.client.get('/api/v1.0/stats')
        expected_status = dict(
            status='working',
            queue_length=0,
            running=1,
            fast=0,
            total_jobs=89132,
            ts_queued=None,
            ts_queued_m=None,
            ts_fast=None,
            ts_fast_m=None,
        )
        self.assertEquals(rv.json, expected_status)


    def test_current_notices(self):
        "Test if current notices are displayed"
        rv = self.client.get('/api/v1.0/news')
        self.assertEquals(rv.json, dict(notices=[]))
        n = Notice(u'Teaser', u'Text')
        redis_store = self._ctx.g._database
        redis_store.hmset(u'notice:%s' % n.id, n.json)
        rv = self.client.get('/api/v1.0/news')
        self.assertEquals(rv.json, dict(notices=[n.json]))
