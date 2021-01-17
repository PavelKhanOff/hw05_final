from django.test import TestCase

from posts.models import Group, Post, User


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
            group=cls.group,

        )

    def test_text_verbose(self):
        """verbose_name поля text и group совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Твой лучший текст!',
            'group': 'Группа!'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text поля text и group совпадает с ожидаемым."""
        field_help_text = {
            'text': 'Пишите без ошибок',
            'group': 'Группа, в которой опубликуется ваш пост.'
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    self.post._meta.get_field(value).help_text, expected)

    def test_post_text(self):
        """Тест отображения __str__ для text"""
        text = self.post.text[:15]
        self.assertEquals(text, self.post.text[:15])

    def test_title_group(self):
        """Тест отображения __str__ для group"""
        title_group = self.group.title
        self.assertEquals(title_group, self.group.title)
