from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_tech_page_accessible_by_name(self):
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, 200)

    def test_author_page_accessible_by_name(self):
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, 200)

    def test_tech_page_uses_correct_template(self):
        response = self.guest_client.get(reverse('about:tech'))
        self.assertTemplateUsed(response, 'about/tech.html')

    def test_author_page_uses_correct_template(self):
        response = self.guest_client.get(reverse('about:author'))
        self.assertTemplateUsed(response, 'about/author.html')
