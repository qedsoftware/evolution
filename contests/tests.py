from django.test import TestCase

from .models import Contest, ContestFactory

class ContestFactoryTest(TestCase):
    def test_create(self):
        factory = ContestFactory()
        factory.name = "test test test"
        factory.code = "test"
        factory.description = "This is a test contest."
        factory.create()
        from_db = Contest.objects.get()
        self.assertEqual(from_db.code, "test")
        self.assertEqual(from_db.name, "test test test")


    def test_from_dict(self):
        factory = ContestFactory.from_dict({'name': 'contest name',
            'code': 'contest_code', 'description': 'hurr durr'})
        factory.create()
        from_db = Contest.objects.get()
        self.assertEqual(from_db.code, "contest_code")
        self.assertEqual(from_db.name, "contest name")
