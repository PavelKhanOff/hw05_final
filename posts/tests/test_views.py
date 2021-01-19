import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User

GROUP1_TITLE = 'testgroup'
GROUP1_DESCRIPTION = 'testdesc'
GROUP1_SLUG = 'testslug'
GROUP2_TITLE = 'secondgroup'
GROUP2_DESCRIPTION = 'newgroupdesc'
GROUP2_SLUG = 'secondtestslug'
USERNAME = 'pavel'
USERNAME_TESTUSER = 'TestUser'
USERNAME_FOR_SUBS = 'testuserforsubs'
LOGIN = reverse('login')
INDEX_URL = reverse('index')
GROUP_URL = reverse('group', args=[GROUP1_SLUG])
PROFILE_URL = reverse('profile', args=[USERNAME])
FOLLOW_INDEX_URL = reverse('follow_index')
PROFILE_FOLLOW_PAVEL_URL = reverse('profile_follow', args=[USERNAME])
PROFILE_UNFOLLOW_PAVEL_URL = reverse('profile_unfollow', args=[USERNAME])
PROFILE_UNFOLLOW_URL = reverse('profile_unfollow', args=[USERNAME])
LOGIN_URL = LOGIN
NEW_POST_URL = reverse('new_post')
SECOND_INDEX_PAGE_URL = INDEX_URL + '?page=2'
SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый супер текст',
            author=User.objects.create(username=USERNAME),
            group=Group.objects.create(title=GROUP1_TITLE,
                                       description=GROUP1_DESCRIPTION,
                                       slug=GROUP1_SLUG),
            image=uploaded
            )
        cls.group = cls.post.group
        Group.objects.create(title=GROUP2_TITLE,
                             description=GROUP2_DESCRIPTION,
                             slug=GROUP2_SLUG)
        cls.POST_URL = reverse('post', args=[cls.post.author.username,
                                             cls.post.id])
        cls.POST_EDIT_URL = reverse('post_edit',
                                    args=[
                                        cls.post.author.username,
                                        cls.post.id])
        cls.ADD_COMMENT_URL = reverse('add_comment',
                                      args=[
                                          cls.post.author.username,
                                          cls.post.id])
        cls.author_testuser = User.objects.create_user(username='TestUser')
        cls.POST_EDIT_TESTUSER_URL = reverse('post_edit',
                                             args=[
                                                 cls.author_testuser.username,
                                                 cls.post.id])
        cls.LOGIN_URL_TESTUSER_URL = (f'{LOGIN_URL}?next='
                                      f'{cls.POST_EDIT_TESTUSER_URL}')
        cls.guest_client = Client()
        cls.user = cls.author_testuser
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_all_pages_contain_correct_context(self):
        cache.clear()
        Follow.objects.create(author=self.post.author,
                              user=self.author_testuser)
        subscriptable_urls = [
            [INDEX_URL, self.guest_client],
            [GROUP_URL, self.guest_client],
            [PROFILE_URL, self.guest_client],
            [self.POST_URL, self.guest_client],
            [FOLLOW_INDEX_URL, self.authorized_client],
        ]
        for url, client in subscriptable_urls:
            with self.subTest():
                response = client.get(url)
                if 'page' in response.context:
                    response_context = response.context['page'][0]
                    self.assertEqual(len(response.context['page']), 1)
                else:
                    response_context = response.context['post']
                self.assertEqual(response_context, self.post)

    def test_first_page_contains_ten_posts(self):
        """Страница содержит 10 записей"""
        for post in range(13):
            Post.objects.create(
                text=f'Тестовый супер текст{post}',
                author=User.objects.create(
                    username=f'{self.post.author.username}{post}'),
            )
        response = self.authorized_client.get(INDEX_URL)
        self.assertEqual(len(response.context['page']), 10)

    def test_second_page_contains_ten_posts(self):
        """Страница номер 2 содержит 4 записи"""
        for post in range(13):
            Post.objects.create(
                text=f'Тестовый супер текст{post}',
                author=User.objects.create(
                    username=f'{self.post.author.username}{post}'),
            )
        response = self.authorized_client.get(SECOND_INDEX_PAGE_URL)
        self.assertEqual(len(response.context['page']), 4)

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
        self.assertNotEqual(
            response_after.content,
            response_after_clear.content
        )

    def test_new_post_not_exists_unsubscribed_person(self):
        """Тестирование того, что новая запись пользователя
        не появится в ленте"""
        response = self.authorized_client.get(FOLLOW_INDEX_URL)
        self.assertEqual(len(response.context['page']), 0)

    def test_authorized_user_can_subscribe(self):
        """Тест на то, что авторизированный
        пользователь может подписываться"""
        self.authorized_client.get(PROFILE_FOLLOW_PAVEL_URL)
        follow = Follow.objects.first()
        self.assertTrue(
            Follow.objects.filter(author=self.post.author,
                                  user=self.author_testuser).exists())
        self.assertEqual(follow.user, self.author_testuser)

    def test_authorized_user_can_unsubscribe(self):
        """Тест на то, что авторизированный
                        пользователь может отписываться"""
        Follow.objects.create(user=self.author_testuser,
                              author=self.post.author)
        self.authorized_client.get(PROFILE_UNFOLLOW_PAVEL_URL)
        self.assertFalse(
            Follow.objects.filter(
                author=self.post.author,
                user=self.author_testuser).exists())
