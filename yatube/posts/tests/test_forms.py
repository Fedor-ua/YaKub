from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post, User

GROUP_SLUG = 'test_slug'
USERNAME_AUTHOR = 'Authortest'
POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile',
                      kwargs={'username': USERNAME_AUTHOR})


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Random_Client')
        cls.author = User.objects.create_user(username=USERNAME_AUTHOR)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',)
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текст',)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)
        self.authorized_client_no_author = Client()
        self.authorized_client_no_author.force_login(self.user)

    def test_create_post_form(self):
        '''Форма создаёт запись'''
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id,
            'author': self.post.author,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)

        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': USERNAME_AUTHOR}))

        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(post.author, self.author)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(form_data.get('group'), self.post.group.id)
        self.assertEqual(form_data.get('author'), self.post.author)

    def test_edit_post_form(self):
        '''Форма редактирует запись'''
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args={self.post.id}),
            data={'text': self.post.text, 'group': self.group.id, },
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)

        self.assertEqual(self.post.text, form_data['text'])
        self.assertEqual(self.post.group.pk, form_data['group'])

    def test_guest_redirect(self):
        '''Редирект гостя на страницу авторизации'''
        response_guest = self.guest_client.get(reverse('posts:post_create'))

        self.assertRedirects(response_guest,
                             reverse('users:login') + '?next='
                             + reverse('posts:post_create'),)

    def test_guest_cant_create_post(self):
        '''Гость не может создавать записи.'''
        reverse_name = reverse('posts:post_create')
        response = self.client.post(reverse_name)
        login = reverse(settings.LOGIN_URL)
        self.assertRedirects(
            response,
            f'{login}?{REDIRECT_FIELD_NAME}={reverse_name}',
            HTTPStatus.FOUND
        )

    def test_comment_for_registered_users(self):
        '''Комментарии могут оставлять зарегистрированные пользователи.'''
        roles = (
            self.authorized_client.post,
            self.authorized_client_no_author.post,
        )
        for role in roles:
            with self.subTest(role=role):
                comment_data = {
                    'text': 'тестовый коммент',
                }
                response = role(
                    reverse('posts:add_comment', args=(self.post.id,)),
                    data=comment_data,
                    follow=True,
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertRedirects(response, reverse(
                    'posts:post_detail', args=(self.post.id,)),
                    HTTPStatus.FOUND
                )
                comment = Comment.objects.first()
                self.assertEqual(comment.text, comment.text)
        self.assertEqual(Comment.objects.count(), 2)

    def test_comment_cant_comment(self):
        '''Комментарии не могут оставлять гости.'''
        comment_count = Comment.objects.count()
        comment_data = {
            'text': 'тестовый коммент',
        }
        reverse_name = reverse('posts:add_comment', args=(self.post.id,))
        response = self.client.post(
            reverse_name,
            data=comment_data,
            follow=True,
        )
        login = reverse(settings.LOGIN_URL)
        self.assertRedirects(
            response,
            f'{login}?{REDIRECT_FIELD_NAME}={reverse_name}',
            HTTPStatus.FOUND
        )
        self.assertEqual(Comment.objects.count(), comment_count)
