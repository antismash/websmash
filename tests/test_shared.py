# -*- coding: utf-8 -*-
from flaskext.testing import TestCase
import os
import tempfile
import shutil
import websmash

class ModelTestCase(TestCase):

    def create_app(self):
        self.app = websmash.app
        self.dl = websmash.dl
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        websmash.mail.suppress = True
        return self.app

    def setUp(self):
        self.db = websmash.db
        self.db.create_all()

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()

class WebsmashTestCase(ModelTestCase):

    def create_app(self):
        return super(WebsmashTestCase, self).create_app()

    def setUp(self):
        super(WebsmashTestCase, self).setUp()
        self.tmpdir = tempfile.mkdtemp()
        (fd, self.tmp_name) = tempfile.mkstemp(dir=self.tmpdir, suffix='.fa')
        self.tmp_file = os.fdopen(fd, 'w+b')
        self.tmp_file.write('>test\nATGACCGAGAGTACATAG\n')
        self.app.config['RESULTS_PATH'] = self.tmpdir

    def tearDown(self):
        super(WebsmashTestCase, self).tearDown()
        self.tmp_file.close()
        shutil.rmtree(self.tmpdir)

