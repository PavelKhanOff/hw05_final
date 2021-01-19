from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

GROUP_TITLE = 'testgroup'
GROUP_DESCRIPTION = 'testdesc'
GROUP_SLUG = 'testslug'
USERNAME = 'pavel'
USERNAME_TESTUSER = 'TestUser'
POST_PAVEL_TEXT = 'Тестовый супер текст'
POST_TESTUSER_TEXT = 'Тестовый супер текст2'
LOGIN = reverse('login')
INDEX_URL = reverse('index')
GROUP_URL = reverse('group', args=[GROUP_SLUG])
PROFILE_URL = reverse('profile', args=[USERNAME])
FOLLOW_INDEX_URL = reverse('follow_index')
PROFILE_FOLLOW_URL = reverse('profile_follow', args=[USERNAME])
PROFILE_UNFOLLOW_URL = reverse('profile_unfollow', args=[USERNAME])
LOGIN_URL = LOGIN
NOT_EXISTING_PAGE_URL = '/not/existing/page'
NEW_POST_URL = reverse('new_post')
LOGIN_URL_NEW_URL = f'{LOGIN_URL}?next={NEW_POST_URL}'
LOGIN_URL_FOLLOW_URL = f'{LOGIN_URL}?next={PROFILE_FOLLOW_URL}'
LOGIN_URL_UNFOLLOW_URL = f'{LOGIN_URL}?next={PROFILE_UNFOLLOW_URL}'


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_pavel = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE, description=GROUP_DESCRIPTION, slug=GROUP_SLUG)
        cls.post_pavel = Post.objects.create(
            text=POST_PAVEL_TEXT,
            author=cls.author_pavel,
            group=cls.group,)
        cls.author_testuser = User.objects.create_user(
            username=USERNAME_TESTUSER)
        cls.post_testuser = Post.objects.create(
            text=POST_TESTUSER_TEXT,
            author=cls.author_testuser,
        )
        cls.POST_URL = reverse('post',
                               args=[cls.author_pavel.username,
                                     cls.post_pavel.id])
        cls.POST_EDIT_URL = reverse(
            'post_edit', args=[cls.author_pavel.username, cls.post_pavel.id])
        cls.POST_EDIT_AUTHOR_URL = reverse('post_edit',
                                           args=[cls.author_testuser.username,
                                                 cls.post_testuser.id])
        cls.ADD_COMMENT_URL = reverse('add_comment',
                                      args=[cls.author_pavel.username,
                                            cls.post_pavel.id])
        cls.LOGIN_URL_TESTUSER_URL = (LOGIN_URL + '?next=' +
                                      cls.POST_EDIT_AUTHOR_URL)
        cls.LOGIN_URL_COMMENT_URL = f'{LOGIN_URL}?next={cls.ADD_COMMENT_URL}'
        cls.guest_client = Client()
        cls.user = cls.author_testuser
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_status_code_for_all_users_and_pages(self):
        url_names = [
            [INDEX_URL, self.guest_client, 200],
            [GROUP_URL, self.guest_client, 200],
            [PROFILE_URL, self.guest_client, 200],
            [FOLLOW_INDEX_URL, self.guest_client, 302],
            [PROFILE_FOLLOW_URL, self.guest_client, 302],
            [PROFILE_UNFOLLOW_URL, self.guest_client, 302],
            [self.POST_URL, self.guest_client, 200],
            [NEW_POST_URL, self.guest_client, 302],
            [self.POST_EDIT_URL, self.guest_client, 302],
            [self.ADD_COMMENT_URL, self.guest_client, 302],
            [NOT_EXISTING_PAGE_URL, self.guest_client, 404],
            [PROFILE_FOLLOW_URL, self.authorized_client, 302],
            [PROFILE_UNFOLLOW_URL, self.authorized_client, 302],
            [NEW_POST_URL, self.authorized_client, 200],
            [self.POST_EDIT_URL, self.authorized_client, 302],
            [self.POST_EDIT_AUTHOR_URL, self.authorized_client, 200],
            [self.ADD_COMMENT_URL, self.authorized_client, 200],
        ]
        for url, client, expected_status_code in url_names:
            with self.subTest():
                self.assertEqual(client.get(url).status_code,
                                 expected_status_code)

    def test_urls_correct_templates(self):
        """Проверка шаблона для адресов"""
        correct_templates_and_adresses = [
            [INDEX_URL, 'index.html'],
            [GROUP_URL, 'group.html'],
            [NEW_POST_URL, 'new_post.html'],
            [self.POST_EDIT_AUTHOR_URL, 'new_post.html'],
            [FOLLOW_INDEX_URL, 'follow.html'],
            [self.ADD_COMMENT_URL, 'comments.html'],
            [self.POST_URL, 'post.html'],
            [PROFILE_URL, 'profile.html'],
        ]
        for url, template in correct_templates_and_adresses:
            with self.subTest():
                self.assertTemplateUsed(self.authorized_client.get(url),
                                        template)

    def test_post_edit_correct_redirect(self):
        correct_pathes_to_redirect = [
            [self.POST_EDIT_AUTHOR_URL, self.guest_client,
             self.LOGIN_URL_TESTUSER_URL],
            [self.POST_EDIT_URL, self.authorized_client, self.POST_URL],
            [NEW_POST_URL, self.guest_client, LOGIN_URL_NEW_URL],
            [self.ADD_COMMENT_URL, self.guest_client,
             self.LOGIN_URL_COMMENT_URL],
            [PROFILE_FOLLOW_URL, self.guest_client, LOGIN_URL_FOLLOW_URL],
            [PROFILE_UNFOLLOW_URL, self.guest_client, LOGIN_URL_UNFOLLOW_URL],
            ]
        for url, client, redirect in correct_pathes_to_redirect:
            self.assertRedirects(client.get(url), redirect)
