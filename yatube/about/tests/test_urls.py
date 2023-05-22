from django.test import Client, TestCase


class StaticPagesURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /page/about/."""
        response_author = self.guest_client.get('/about/author/')
        self.assertEqual(response_author.status_code, 200)
        response_tech = self.guest_client.get('/about/tech/')
        self.assertEqual(response_tech.status_code, 200)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблона для адреса /page/about/."""
        response_author = self.guest_client.get('/about/author/')
        self.assertTemplateUsed(response_author, 'about/author.html')
        response_tech = self.guest_client.get('/about/tech/')
        self.assertTemplateUsed(response_tech, 'about/tech.html')
