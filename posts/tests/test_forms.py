import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post, User

USERNAME = 'pavel'
GROUP_SLUG = 'testslug'
GROUP_TITLE = 'Тестовая группа'
GROUP_DESCRIPTION = "Описание тестовой группы"
POST_TEXT = "Тестовый текст должен быть очень длинным"
NEW_POST_URL = reverse("new_post")
INDEX_URL = reverse("index")
LOGIN_URL = '/auth/login/'
NEW_POST_REDIRECT_URL = LOGIN_URL+'?next='+NEW_POST_URL
SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B')


class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.guest_client = Client()
        cls.user_pavel = User.objects.create(username=USERNAME)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_pavel)
        cls.group = Group.objects.create(
            slug=GROUP_SLUG,
            title=GROUP_TITLE,
            description=GROUP_DESCRIPTION,
            )
        cls.post = Post.objects.create(
            author=cls.user_pavel,
            text=POST_TEXT,
            group=cls.group,
            image=uploaded
        )
        cls.POST_EDIT_URL = (reverse("post_edit",
                                     kwargs={"username": cls.user_pavel,
                                             "post_id": cls.group.id}))
        cls.POST_URL = reverse('post', kwargs={
            'username': cls.user_pavel.username, 'post_id': cls.post.id})
        cls.ADD_COMMENT_URL = reverse('add_comment', kwargs={
            'username': cls.user_pavel.username,
            'post_id': cls.post.id})
        cls.POST_REDIRECT_URL = LOGIN_URL + '?next=' + cls.POST_EDIT_URL

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post_authorized(self):
        """Валидная форма создает запись в Post
        авторизированным пользователя"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Текст новой записи",
            "group": "",
        }
        response = self.authorized_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, INDEX_URL)
        self.assertEqual(Post.objects.count(), post_count+1)

    def test_create_post_not_authorized(self):
        """Валидная форма не создает запись в Post
        неавторизированным пользователя"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Текст новой записи",
            "group": "",
        }
        response = self.guest_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, NEW_POST_REDIRECT_URL)
        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_post_authorized(self):
        """Редактируется нужный пост авторизированным пользователя"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Измененный текст новой записи",
            "group": self.group.id,
        }
        response = self.authorized_client.post(self.POST_EDIT_URL,
                                               data=form_data,
                                               follow=True)
        self.assertRedirects(response, self.POST_URL)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(Post.objects.filter
                        (text="Измененный текст новой записи").exists())

    def test_edit_post_not_authorized(self):
        """Редактируется нужный пост авторизированным пользователя"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Измененный текст новой записи",
            "group": self.group.id,
        }
        response = self.guest_client.post(self.POST_EDIT_URL,
                                          data=form_data,
                                          follow=True)
        self.assertRedirects(response, self.POST_REDIRECT_URL)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(Post.objects.filter(
            text="Измененный текст новой записи").exists())

    def test_comment_post(self):
        """Авторизированный пользователь может комментировать посты"""
        form_data = {
            'post': self.post,
            'author': self.user_pavel,
            'text': 'тестовый комментарий'
        }
        response = self.authorized_client.post(self.ADD_COMMENT_URL,
                                               data=form_data,
                                               follow=True
                                               )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, form_data['author'])
        self.assertRedirects(response, self.POST_URL)
        self.assertEqual(self.post.comments.count(), 1)
        self.assertEqual(comment.post, self.post)

    def test_new_post_and_post_edit_pages_correct_fields(self):
        """Страница создания нового поста и
        редактирования поста использует правильные поля"""
        response = self.authorized_client.get(NEW_POST_URL)
        form_fields = [
            ['group', forms.fields.ChoiceField],
            ['text', forms.fields.CharField],
        ]
        for page, field in form_fields:
            with self.subTest():
                form_field = response.context['form'].fields.get(page)
                self.assertIsInstance(form_field, field)
