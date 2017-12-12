from websmash.models import Notice
from tests.test_shared import ModelTestCase


class NoticeTestCase(ModelTestCase):
    def test_notice_instantiate(self):
        "Test if Notice can be instantiated"
        notice = Notice(u'test teaser', u'test text')
        assert notice

    def test_notice_repr(self):
        "Test if Notice repr matches the data"
        notice = Notice(u'test teaser', u'test text')
        assert notice.teaser in str(notice)
        assert notice.category in str(notice)

    def test_json(self):
        "Test if Notice json property matches the data"
        notice = Notice(u'test teaser', u'test text')
        d = notice.json
        fmt = "%Y-%m-%d %H:%M:%S"
        self.assertEquals(d['category'], notice.category)
        self.assertEquals(d['teaser'], notice.teaser)
        self.assertEquals(d['text'], notice.text)
        self.assertEquals(d['added'], notice.added.strftime(fmt))
        self.assertEquals(d['show_from'], notice.show_from.strftime(fmt))
        self.assertEquals(d['show_until'], notice.show_until.strftime(fmt))
