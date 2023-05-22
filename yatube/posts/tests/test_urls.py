from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()

SIGN_UP_URL = '/auth/signup/'
LOGIN_URL = '/auth/login/'
LOGOUT_URL = '/auth/logout/'


class StaticURLTests(TestCase):
    def test_main_page(self):
        guest_client = Client()
        response = guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestPostList(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Random_Client')
        cls.author = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            description='Тестовое описание группы',
            slug='test-group-slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тест',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user)

    def tearDown(self):
        del self.guest_client
        del self.authorized_client

    def test_template_page(self):
        user_name = self.author.username
        post_id = self.post.id
        slug = self.group.slug

        templates = {
            reverse('posts:main_view'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': user_name}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': post_id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': post_id}):
            'posts/create_post.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }
        for rev_address, template in templates.items():
            with self.subTest(rev_address=rev_address):
                response = self.authorized_client.get(rev_address)
                self.assertTemplateUsed(response, template)

    def test_unexist_page(self):
        response = self.authorized_client.get('/unexist_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_existence_guest_url(self):
        '''Проверка доступности urls для неавторизованных пользователей'''
        urls = (SIGN_UP_URL, LOGIN_URL)
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_url_correct_template(self):
        '''Проверка шаблонов для неавторизованных пользователей'''
        templates = {
            SIGN_UP_URL: 'users/signup.html',
            LOGIN_URL: 'users/login.html',
        }
        for url, template in templates.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_existence_authorized_url(self):
        '''Проверка доступности urls для авторизованных пользователей'''
        response = self.authorized_client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_url_correct_template(self):
        '''Проверка шаблонов для авторизованных пользователей'''
        response = self.authorized_client.get(LOGOUT_URL)
        self.assertTemplateUsed(response, 'users/logged_out.html')

    def test_404_nonexistent_page(self):
        '''Проверка 404 для несуществующих страниц.'''
        url = '/unexisting_page/'
        roles = (
            self.authorized_client,
            self.authorized_client_no_author,
            self.client,
        )
        for role in roles:
            with self.subTest(url=url):
                response = role.get(url, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
                self.assertTemplateUsed(response, 'core/404.html')
