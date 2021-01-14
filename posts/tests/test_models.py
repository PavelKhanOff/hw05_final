from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='testgrouptitle',
            description='testdesc',
            slug='testslug',
        )
        cls.post = Post.objects.create(
            text='Тестовый супер текст',
            author=User.objects.create(username='testuser'),
            group=Group.objects.get(id=cls.group.id),

        )

    def test_text_verbose(self):
        """verbose_name поля text и group совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Твой лучший текст!',
            'group': 'Группа!'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text поля text и group совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_text = {
            'text': 'Пиши без ошибок плз',
            'group': 'Выбери группу!'
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_post_text(self):
        """Тест отображения __str__ для text"""
        post = PostModelTest.post
        text = post.text[:15]
        self.assertEquals(text, self.post.text[:15])

    def test_title_group(self):
        """Тест отображения __str__ для group"""
        group = PostModelTest.group
        title_group = group.title
        self.assertEquals(title_group, self.group.title)
