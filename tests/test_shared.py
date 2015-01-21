# -*- coding: utf-8 -*-
from flask.ext.testing import TestCase
import os
import tempfile
import shutil
from mockredis import mock_redis_client
import websmash

class ModelTestCase(TestCase):

    def create_app(self):
        self.app = websmash.app
        self.dl = websmash.dl
        self.app.config['TESTING'] = True
        websmash.mail.suppress = True
        self.app.config['FAKE_DB'] = True
        return self.app

    def setUp(self):
        pass

    def tearDown(self):
        pass

class WebsmashTestCase(ModelTestCase):

    def create_app(self):
        return super(WebsmashTestCase, self).create_app()

    def setUp(self):
        super(WebsmashTestCase, self).setUp()
        self.tmpdir = tempfile.mkdtemp()
        (fd, self.tmp_name) = tempfile.mkstemp(dir=self.tmpdir, suffix='.fa')
        tmp_file = os.fdopen(fd, 'w+b')
        tmp_file.write('>test\nATGACCGAGAGTACATAG\n')
        tmp_file.close()
        self.tmp_file = open(self.tmp_name, 'r')

        self.app.config['RESULTS_PATH'] = self.tmpdir

    def tearDown(self):
        super(WebsmashTestCase, self).tearDown()
        self.tmp_file.close()
        shutil.rmtree(self.tmpdir)

