import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User

INDEX_URL = reverse('index')
GROUP_URL = reverse('group', kwargs={'slug': 'testslug'})
PROFILE_URL = reverse('profile', kwargs={'username': 'pavel'})
FOLLOW_INDEX_URL = reverse('follow_index')
PROFILE_FOLLOW_URL = reverse('profile_follow', kwargs={
            'username': 'testuserforsubs'})
PROFILE_FOLLOW_PAVEL_URL = reverse('profile_follow', kwargs={
            'username': 'pavel'})
PROFILE_UNFOLLOW_URL = reverse('profile_unfollow',
                               kwargs={'username': 'pavel'})
LOGIN_URL_TESTUSER_URL = '/auth/login/?next=/TestUser/2/edit/'


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый супер текст',
            author=User.objects.create(username='pavel'),
            group=Group.objects.create(title='testgroup',
                                       description='testdesc',
                                       slug='testslug'),
            image=uploaded
            )
        cls.group = cls.post.group
        Group.objects.create(title='secondgroup',
                             description='newgroupdesc',
                             slug='secondtestslug')
        cls.POST_URL = reverse('post', kwargs={
            'username': cls.post.author.username, 'post_id': cls.post.id})
        cls.NEW_POST_URL = reverse('new_post')
        cls.POST_EDIT_URL = reverse('post_edit', kwargs={
            'username': cls.post.author.username,
            'post_id': cls.post.id})
        cls.ADD_COMMENT_URL = reverse('add_comment', kwargs={
            'username': cls.post.author.username,
            'post_id': cls.post.id})

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_all_pages_contain_correct_context(self):
        @override_settings(
            CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.'
                                           'DummyCache'}})
        # после использования cache тест INDEX_URL упал,
        # я применил override_settings, если так делать нельзя,
        # прошу объяснить почему.
        def test():
            pages = [
                [INDEX_URL, self.guest_client, self.post],
                [GROUP_URL, self.guest_client, self.post],
                [PROFILE_URL, self.guest_client, self.post],
                [self.POST_URL, self.guest_client, self.post],
                [INDEX_URL, self.authorized_client, self.post],
                [GROUP_URL, self.authorized_client, self.post],
                [PROFILE_URL, self.authorized_client, self.post],
                [self.POST_URL, self.authorized_client, self.post],
            ]
            for url in pages:
                with self.subTest():
                    response = url[1].get(url[0])
                    actual_post = response.context.get('post')
                    self.assertEqual(actual_post, url[2])

    def test_new_post_and_post_edit_pages_correct_context(self):
        """Страница создания нового поста и
        редактирования поста использует правильный context"""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = [
            ['group', forms.fields.ChoiceField],
            ['text', forms.fields.CharField],
        ]
        for field in form_fields:
            with self.subTest():
                form_field = response.context.get('form').fields.get(field[0])
                self.assertIsInstance(form_field, field[1])

    def test_first_page_contains_ten_posts(self):
        """Страница содержит 10 записей"""
        for post in range(13):
            Post.objects.create(
                text=f'Тестовый супер текст{post}',
                author=User.objects.create(
                    username=f'{self.post.author.username}{post}'),
            )
        response = self.authorized_client.get(INDEX_URL)
        self.assertEqual(len(response.context.get('page')), 10)

    def test_second_page_contains_ten_posts(self):
        """Страница номер 2 содержит 4 записи"""
        for post in range(13):
            Post.objects.create(
                text=f'Тестовый супер текст{post}',
                author=User.objects.create(
                    username=f'{self.post.author.username}{post}'),
            )
        response = self.authorized_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page')), 4)

    def test_index_page_uses_cache(self):
        """Главная страница использует кэш."""
        response_before = self.guest_client.get(INDEX_URL)
        self.test_cache_post = Post.objects.create(
            text='Пост для теста кэша',
            author=self.user,
            group=self.group
        )
        response_after = self.guest_client.get(INDEX_URL)
        self.assertEqual(
            response_before.content,
            response_after.content
        )
        cache.clear()
        response_after_clear = self.guest_client.get(
            INDEX_URL
        )
        self.assertEqual(
            response_after_clear.context['page'][0],
            self.test_cache_post
        )

    def test_new_post_exists_subscribed_person(self):
        """Тестирование того, что новая запись пользователя появится
         в ленте тех кто на него подписан"""
        new_post = Post.objects.create(
            text='Новый супер текст',
            author=User.objects.create(
                username='testuserforsubs'),
        )
        self.authorized_client.get(PROFILE_FOLLOW_URL)
        response = self.authorized_client.get(FOLLOW_INDEX_URL)
        expected_post = new_post
        actual_post = response.context.get('page')[0]
        self.assertEqual(actual_post, expected_post)

    def test_authorized_user_can_subscribe(self):
        """Тест на то, что только авторизированный
                        пользователь может подписываться"""
        before_sub = Follow.objects.all().count()
        self.authorized_client.get(PROFILE_FOLLOW_PAVEL_URL)
        after_sub = Follow.objects.all().count()
        self.assertNotEqual(before_sub, after_sub)

    def test_authorized_user_can_unsubscribe(self):
        """Тест на то, что только авторизированный
                        пользователь может отписываться"""
        self.authorized_client.get(PROFILE_FOLLOW_PAVEL_URL)
        after_sub = Follow.objects.all().count()
        self.authorized_client.get(PROFILE_UNFOLLOW_URL)
        after_unsub = Follow.objects.all().count()
        self.assertNotEqual(after_sub, after_unsub)
