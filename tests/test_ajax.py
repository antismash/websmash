# -*- coding: utf-8 -*-
from websmash.models import Job, Notice
from tests.test_shared import WebsmashTestCase

class AjaxTestCase(WebsmashTestCase):
    def test_server_status(self):
        """Test if server status returns the correct values"""
        rv = self.client.get('/server_status')
        self.assertEquals(rv.json, dict(status='idle', queue_length=0, running=0, long_running=0))
        j = Job()
        redis_store = self._ctx.g._database
        redis_store.hmset(u'job:%s' % j.uid, j.get_dict())
        redis_store.lpush('jobs:queued', j.uid)
        rv = self.client.get('/server_status')
        self.assertEquals(rv.json, dict(status='working', queue_length=1, running=0, long_running=0))
        redis_store.rpoplpush('jobs:queued', 'jobs:timeconsuming')
        rv = self.client.get('/server_status')
        self.assertEquals(rv.json, dict(status='working', queue_length=0, running=0, long_running=1))
        j.status="running: not really"
        redis_store.rpoplpush('jobs:timeconsuming', 'jobs:running')
        rv = self.client.get('/server_status')
        self.assertEquals(rv.json, dict(status='working', queue_length=0, running=1, long_running=0))


    def test_current_notices(self):
        "Test if current notices are displayed"
        rv = self.client.get('/current_notices')
        self.assertEquals(rv.json, dict(notices=[]))
        n = Notice(u'Teaser', u'Text')
        redis_store = self._ctx.g._database
        redis_store.hmset(u'notice:%s' % n.id, n.json)
        rv = self.client.get('/current_notices')
        self.assertEquals(rv.json, dict(notices=[n.json]))
