import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class TestForms(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B'
                     )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.posts_count = Post.objects.count()
        cls.post = Post.objects.create(
            text='Тестовый супер текст',
            author=User.objects.create(username='testuser'),
            group=Group.objects.create(title='testgroup'),
            image=uploaded,
            )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()

    def test_create_form(self):
        """Отправка формы создает новую запись в базе данных"""
        self.assertEqual(Post.objects.count(), self.posts_count+1)

    def test_post_saved(self):
        """Отправка формы сохраняет запись в базе данных"""
        self.assertTrue(Post.objects.filter(
            text=self.post.text).exists())

    def test_post_updated(self):
        """Изменения поста сохраняются в базе данных"""
        update = Post.objects.get(id=self.post.id)
        update.text = 'Изменённый текст'
        update.save()
        self.assertEqual(Post.objects.get(id=self.post.id).text,
                         'Изменённый текст')
