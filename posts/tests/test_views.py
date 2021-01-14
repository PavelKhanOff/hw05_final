import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


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
                     b'\x0A\x00\x3B'
                     )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый супер текст',
            author=User.objects.create(username='testauthor'),
            group=Group.objects.create(title='testgroup',
                                       description='testdesc',
                                       slug='testslug'),
            image=uploaded
            )
        cls.group = Group.objects.get(slug='testslug')
        Group.objects.create(title='secondgroup',
                             description='newgroupdesc',
                             slug='secondtestslug')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testuser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_correct_template(self):
        """URL-адреса использует правильные шаблоны"""
        templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={'slug': 'testslug'}),
            'new_post.html': reverse('new_post'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_group_page_correct_context_authorized_user(self):
        """Тест правильного контекста для home_page
        и group_page авторизированным пользователем"""

        right_context = {
            PostViewsTest.post: [reverse('index'),
                                 reverse('group', kwargs={'slug': 'testslug'})]
        }
        for context, reverse_name in right_context.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name[0])
                actual_post = response.context.get('page')[0]
                self.assertEqual(actual_post, context)
                response_group = self.authorized_client.get(reverse_name[1])
                actual_post_group = response_group.context.get('page')[0]
                self.assertEqual(actual_post_group, context)

    def test_home_page_group_page_correct_context_unauthorized_user(self):
        """Тест правильного контекста для home_page
                и group_page неавторизированным пользователем"""

        right_context = {
            PostViewsTest.post: [reverse('index'),
                                 reverse('group',
                                         kwargs={'slug': self.group.slug})]
        }
        for context, reverse_name in right_context.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name[0])
                actual_post = response.context.get('page')[0]
                self.assertEqual(actual_post, context)
                response = self.guest_client.get(reverse_name[1])
                actual_post = response.context.get('page')[0]
                self.assertEqual(actual_post, context)

    def test_new_post_and_post_edit_pages_correct_context(self):
        """Страница создания нового поста и
        редактирования поста использует правильный context"""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_profile_page_correct_context_authorized_user(self):
        """Страница профиля использует правильный context
        для авторизированного пользователя"""
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.post.author.username}))
        expected_post = PostViewsTest.post
        actual_post = response.context.get('page')[0]
        self.assertEqual(actual_post, expected_post)

    def test_profile_page_correct_context_unauthorized_user(self):
        """Страница профиля использует правильный context
        для авторизированного пользователя"""
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': self.post.author.username}))
        expected_post = PostViewsTest.post
        actual_post = response.context.get('page')[0]
        self.assertEqual(actual_post, expected_post)

    def test_post_id_page_correct_context_authorized_user(self):
        """Страница поста использует правильный context
        для авторизированного пользователя"""
        response = self.authorized_client.get(reverse('post', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id}))
        expected_post = PostViewsTest.post
        actual_post = response.context.get('post')
        self.assertEqual(actual_post, expected_post)

    def test_post_id_page_correct_context_unauthorized_user(self):
        """Страница поста использует правильный context
        для неавторизированного пользователя"""
        response = self.guest_client.get(reverse('post', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id}))
        expected_post = PostViewsTest.post
        actual_post = response.context.get('post')
        self.assertEqual(actual_post, expected_post)

    def test_first_page_contains_ten_posts(self):
        """Страница содержит 10 записей"""
        for post in range(13):
            Post.objects.create(
                text=f'Тестовый супер текст{post}',
                author=User.objects.create(
                    username=f'{self.post.author.username}{post}'),
            )
        response = self.authorized_client.get(reverse('index'))
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

    def test_image_index_profile_post_group(self):
        """Проверка что при выводе поста с картинкой,
        картинка есть в context"""
        response = self.authorized_client.get(reverse('index'))
        expected_post = PostViewsTest.post
        actual_post = response.context.get('page')[0]
        self.assertEqual(actual_post, expected_post)

    def test_cache(self):
        """Тестирование кэша"""
        post_before = self.guest_client.get('/')
        Post.objects.create(text='текст проверки кэша',
                            author=User.objects.get(username=self.post.author))
        post_after = self.guest_client.get('/')
        self.assertNotEqual(
            post_before.content,
            post_after.content,
            'Контент совпадает'
        )

    def test_new_post_exists_subscribed_person(self):
        """Тестирование того, что новая запись пользователя появится
         в ленте тех кто на него подписан"""
        new_post = Post.objects.create(
                text='Новый супер текст',
                author=User.objects.create(
                    username='testuserforsubs'),
            )
        self.authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': new_post.author.username}))

        response = self.authorized_client.get(reverse('follow_index'))
        expected_post = new_post
        actual_post = response.context.get('page')[0]
        self.assertEqual(actual_post, expected_post)

    def test_authorized_user_can_subscribe(self):
        """Тест на то, что только авторизированный
                        пользователь может подписываться"""
        before_sub = Follow.objects.all().count()
        self.authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': User.objects.get(
                        username='testauthor')}))
        after_sub = Follow.objects.all().count()
        self.assertNotEqual(before_sub, after_sub)

    def test_authorized_user_can_unsubscribe(self):
        """Тест на то, что только авторизированный
                        пользователь может отписываться"""
        self.authorized_client.get(
            reverse('profile_follow',
                    kwargs={'username': User.objects.get(
                        username='testauthor')}))
        after_sub = Follow.objects.all().count()
        self.authorized_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': User.objects.get(
                        username='testauthor')}))
        after_unsub = Follow.objects.all().count()
        self.assertNotEqual(after_sub, after_unsub)
