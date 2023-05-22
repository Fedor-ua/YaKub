from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User, Follow

GROUP_SLUG = 'test_slug'
GROUP2_SLUG = 'test2'
USERNAME = 'ADMIN'
USERNAME_AUTHOR = 'Authortest'
INDEX_URL = reverse('posts:main_view')
POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile',
                      kwargs={'username': USERNAME_AUTHOR})
GROUP_LIST_URL = reverse('posts:group_list',
                         kwargs={'slug': GROUP_SLUG})
GROUP2_LIST_URL = reverse('posts:group_list',
                          kwargs={'slug': GROUP2_SLUG})


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_no_author = User.objects.create_user(username='NoAuthor')
        cls.user = User.objects.create_user(username=USERNAME)
        cls.author = User.objects.create_user(username=USERNAME_AUTHOR)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',)
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug=GROUP2_SLUG,
            description='Тестовое описание 2',)
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текст',
        )
        cls.post_id = cls.post.pk

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    def test_pages_uses_correct_template(self):
        '''URL-адрес использует соответствующий шаблон.'''
        templates_pages_names = {
            reverse('posts:main_view'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': GROUP_SLUG}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': USERNAME_AUTHOR}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post_id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post_id}):
            'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_show_correct_context(self):
        '''Шаблоны сформированы с правильным контекстом.'''
        correct_context = (
            GROUP_LIST_URL,
            INDEX_URL,
            PROFILE_URL,
        )
        for url in correct_context:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if 'page_obj' in response.context:
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.text, self.post.text)

    def test_post_is_not_in_incorrect_page(self):
        '''Проверка, что запись не попала на страницу для
        которой не была предназначена.'''
        urls = (GROUP2_LIST_URL,)
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertNotIn(
                    self.group2,
                    response.context['page_obj'])


class PaginatorTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',)

        Post.objects.bulk_create(
            Post(
                author=self.user,
                text=f'{i + 1} test',
                group=self.group
            )
            for i in range(13)
        )

    def test_1st_page_contains_ten_posts(self):
        '''Проверка кол-ва записей на 1 стр.'''
        response = self.client.get(reverse('posts:main_view'))
        self.assertEqual(len(response.context['page_obj']), settings.PAGE_LIM)

    def test_last_page_contains_x_posts(self):
        '''Проверка кол-ва записей на 2 стр.'''
        num_of_posts_last_page = Post.objects.count() % settings.PAGE_LIM
        response = self.client.get(reverse('posts:main_view') + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         num_of_posts_last_page)


class CacheAndFollowTest(TestCase):
    def setUp(self):
        self.new_author = User.objects.create(username='Follow_Unfollow')
        self.user = User.objects.create(username='Author')
        self.user_no_author = User.objects.create_user(username='NoAuthor')
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user_no_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',)

    def test_cache(self):
        '''Проверка работы кэша.'''
        post = Post.objects.create(
            author=self.user,
            text='Пост для проверки кэша',
            group=self.group
        )
        response_1 = self.client.get(reverse('posts:main_view'))
        self.assertTrue(Post.objects.get(pk=post.id))
        Post.objects.get(pk=post.id).delete()
        cache.clear()
        response_3 = self.client.get(reverse('posts:main_view'))
        self.assertNotEqual(response_1.content, response_3.content)

    def test_users_can_follow(self):
        '''Зарегистрированный пользователь может подписаться.'''
        count_follow = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.new_author.username}
            )
        )
        follow = Follow.objects.last()
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author, self.new_author)
        self.assertEqual(follow.user, self.user)

    def test_users_can_unfollow(self):
        '''Зарегистрированный пользователь может отписаться.'''
        count_follow = Follow.objects.count()
        Follow.objects.create(
            user=self.user_no_author,
            author=self.user
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.authorized_client_no_author.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user.username})
        )
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_post_appears_at_smfeed(self):
        '''Пост появляется в ленте'''
        Follow.objects.create(
            user=self.user_no_author,
            author=self.user
        )
        post = Post.objects.create(
            author=self.user,
            text='Пост для проверки появления в ленте',
        )
        response = self.authorized_client_no_author.get(
            reverse('posts:follow_index')
        )
        self.assertContains(response, post)

    def test_post_do_not_appears_at_smfeed(self):
        '''Не появляется в ленте'''
        Follow.objects.create(
            user=self.user_no_author,
            author=self.user
        )
        post = Post.objects.create(
            author=self.user,
            text='Пост для проверки появления в ленте',
        )
        Follow.objects.filter(
            user=self.user_no_author,
            author=self.user
        ).delete()
        response = self.authorized_client_no_author.get(
            reverse('posts:follow_index')
        )
        self.assertNotContains(response, post)
