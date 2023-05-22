from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост более 15 символов и тест вроде не падает)',
        )

    def test_models_have_correct_object_names(self):
        '''Проверяем отображение поля title'''
        group = self.group
        str_title_group = group.title
        self.assertEqual(str_title_group, str(group))

        '''Проверяем, что у моделей корректно работает __str__'''
        post = self.post
        self.assertEqual(post.text[:settings.LIM_CHAR],
                         str(post),
                         )

    def test_models_have_correct_title_names(self):
        '''У моделей Group и Post корректно работает __str__.'''
        title = (
            (self.group, self.group.title),
            (self.post, self.post.text[:settings.LIM_CHAR]),
        )
        for text, expected_name in title:
            with self.subTest(expected_name=text):
                self.assertEqual(expected_name, str(text))
