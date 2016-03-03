from django.test import TestCase

from .models import Contest, ContestFactory

from system.models import PostData

class ContestFactoryTest(TestCase):
    def test_create(self):
        factory = ContestFactory()
        factory.name = "test test test"
        factory.code = "test"
        factory.description = PostData.from_source("test", "html")
        factory.description.build_html()
        factory.rules = factory.description
        factory.create()
        from_db = Contest.objects.get()
        self.assertEqual(from_db.code, "test")
        self.assertEqual(from_db.name, "test test test")


    def test_from_dict(self):
        description = PostData.from_source("test", "plaintext")
        description.build_html()
        factory = ContestFactory.from_dict({'name': 'contest name',
            'code': 'contest_code', 'description': description,
            'rules': description})
        factory.create()
        from_db = Contest.objects.get()
        self.assertEqual(from_db.code, "contest_code")
        self.assertEqual(from_db.name, "contest name")
