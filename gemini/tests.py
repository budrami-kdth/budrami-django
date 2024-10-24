# yourapp/tests.py
from django.test import TestCase
from django.urls import reverse

class YourAppTests(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_sample_model(self):
        # Assuming you have a model named SampleModel
        from .models import SampleModel
        sample = SampleModel.objects.create(name="Test")
        self.assertEqual(sample.name, "Test")
