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
GROUP2_SLUG = 'testslug2'
GROUP2_TITLE = 'Тестовая группа2'
GROUP2_DESCRIPTION = "Описание тестовой группы2"
POST_TEXT = "Тестовый текст должен быть очень длинным"
NEW_POST_URL = reverse("new_post")
INDEX_URL = reverse('index')
LOGIN_URL = reverse('login')
NEW_POST_REDIRECT_URL = LOGIN_URL+'?next='+NEW_POST_URL
SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B')
SMALL_GIF2 = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
              b'\x01\x00\x80\x00\x00\x00\x00\x00'
              b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
              b'\x01\x00\x80\x00\x00\x00\x00\x00'
              b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
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
        cls.group2 = Group.objects.create(
            slug=GROUP2_SLUG,
            title=GROUP2_TITLE,
            description=GROUP2_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user_pavel,
            text=POST_TEXT,
            group=cls.group,
            image=uploaded
        )
        cls.POST_EDIT_URL = (reverse("post_edit",
                                     args=[cls.user_pavel, cls.post.id]))
        cls.POST_URL = reverse('post', args=[cls.user_pavel.username,
                                             cls.post.id])
        cls.ADD_COMMENT_URL = reverse('add_comment',
                                      args=[cls.user_pavel.username,
                                            cls.post.id])
        cls.POST_REDIRECT_URL = LOGIN_URL + '?next=' + cls.POST_EDIT_URL

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post_authorized(self):
        """Валидная форма создает запись в Post
        авторизированным пользователя"""
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            "text": "Текст новой записи",
            "group": self.group2.id,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            NEW_POST_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.exclude(id=self.post.id)[0]
        self.assertEqual(Post.objects.all().count(), 2)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertTrue(post.image, f'posts/{uploaded.name}')
        self.assertRedirects(response, INDEX_URL)

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
        uploaded2 = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF2,
            content_type='image/gif'
        )
        form_data = {
            "text": "Текст новой записи",
            "group": self.group2.id,
            "image": uploaded2
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data, follow=True
        )
        post_editing = response.context['post']
        self.assertEqual(post_editing.text, form_data['text'])
        self.assertEqual(post_editing.group.id, form_data['group'])
        self.assertEqual(post_editing.image.name, f'posts/{uploaded2.name}')
        self.assertRedirects(response, self.POST_URL)

    def test_edit_post_not_authorized(self):
        """Не редактируется нужный пост неавторизированным пользователя"""
        post_count = Post.objects.count()
        form_data = {
            "text": "Измененный текст новой записи",
            "group": self.group.id,
        }
        response = self.guest_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        post_after_editing = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, self.POST_REDIRECT_URL)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(self.post, post_after_editing)

    def test_comment_post(self):
        """Авторизированный пользователь может комментировать посты"""
        form_data = {
            'text': 'тестовый комментарий'
        }
        response = self.authorized_client.post(self.ADD_COMMENT_URL,
                                               data=form_data,
                                               follow=True
                                               )
        comment = Comment.objects.first()
        self.assertEqual(comment.text, form_data['text'])
        self.assertRedirects(response, self.POST_URL)
        self.assertEqual(Comment.objects.all().count(), 1)
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
            with self.subTest(page=page):
                form_field = response.context['form'].fields.get(page)
                self.assertIsInstance(form_field, field)
