from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

INDEX_URL = reverse('index')
GROUP_URL = reverse('group', kwargs={'slug': 'testslug'})
PROFILE_URL = reverse('profile', kwargs={'username': 'pavel'})
FOLLOW_INDEX_URL = reverse('follow_index')
PROFILE_FOLLOW_URL = reverse('profile_follow', kwargs={
            'username': 'pavel'})
PROFILE_UNFOLLOW_URL = reverse('profile_unfollow',
                               kwargs={'username': 'pavel'})
LOGIN_URL_TESTUSER_URL = '/auth/login/?next=/TestUser/2/edit/'
NOT_EXISTING_PAGE_URL = '/not/existing/page'


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_pavel = User.objects.create_user(username='pavel')
        cls.group = Group.objects.create(
            title='testgroup', description='testdesc', slug='testslug')
        cls.post_pavel = Post.objects.create(
            text='Тестовый супер текст',
            author=cls.author_pavel,
            group=cls.group,)
        cls.author_testuser = User.objects.create_user(username='TestUser')
        cls.post_testuser = Post.objects.create(
            text='Тестовый супер текст2',
            author=cls.author_testuser,
        )
        cls.POST_URL = reverse('post',
                               kwargs={'username': cls.author_pavel.username,
                                       'post_id': cls.post_pavel.id})
        cls.NEW_POST_URL = reverse('new_post')
        cls.POST_EDIT_URL = reverse('post_edit', kwargs={
                                    'username': cls.author_pavel.username,
                                    'post_id': cls.post_pavel.id})
        cls.POST_EDIT_AUTHOR_URL = reverse('post_edit', kwargs={
            'username': cls.author_testuser.username,
            'post_id': cls.post_testuser.id})
        cls.ADD_COMMENT_URL = reverse('add_comment', kwargs={
            'username': cls.author_pavel.username,
            'post_id': cls.post_pavel.id,
        })

    def setUp(self):
        self.guest_client = Client()
        self.user = self.author_testuser
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_status_code_for_all_users_and_pages(self):
        url_names = [
            [INDEX_URL, self.guest_client, 200, 1],
            [GROUP_URL, self.guest_client, 200, 2],
            [PROFILE_URL, self.guest_client, 200, 3],
            [FOLLOW_INDEX_URL, self.guest_client, 302, 4],
            [PROFILE_FOLLOW_URL, self.guest_client, 302, 5],
            [PROFILE_UNFOLLOW_URL, self.guest_client, 302, 6],
            [self.POST_URL, self.guest_client, 200, 7],
            [self.NEW_POST_URL, self.guest_client, 302, 8],
            [self.POST_EDIT_URL, self.guest_client, 302, 9],
            [self.ADD_COMMENT_URL, self.guest_client, 302, 10],
            [NOT_EXISTING_PAGE_URL, self.guest_client, 404, 21],
            [INDEX_URL, self.authorized_client, 200, 11],
            [GROUP_URL, self.authorized_client, 200, 12],
            [PROFILE_URL, self.authorized_client, 200, 13],
            [FOLLOW_INDEX_URL, self.authorized_client, 200, 14],
            [PROFILE_FOLLOW_URL, self.authorized_client, 302, 15],
            [PROFILE_UNFOLLOW_URL, self.authorized_client, 302, 16],
            [self.POST_URL, self.authorized_client, 200, 17],
            [self.NEW_POST_URL, self.authorized_client, 200, 18],
            [self.POST_EDIT_URL, self.authorized_client, 302, 19],
            [self.POST_EDIT_AUTHOR_URL, self.authorized_client, 200, 20],
            [self.ADD_COMMENT_URL, self.authorized_client, 200, 21],
            [NOT_EXISTING_PAGE_URL, self.authorized_client, 404, 21],
        ]
        for url_name in url_names:
            with self.subTest():
                current_status_code = url_name[1].get(url_name[0]).status_code
                self.assertEqual(current_status_code, url_name[2])

    def test_urls_correct_templates(self):
        """Проверка шаблона для адреса '/', '/group/testslug/', '/new',
         /username/post_id/edit."""
        correct_templates_and_adresses = [
            [INDEX_URL, 'index.html'],
            [GROUP_URL, 'group.html'],
            [self.NEW_POST_URL, 'new_post.html'],
            [self.POST_EDIT_AUTHOR_URL, 'new_post.html'],
        ]
        for url_name in correct_templates_and_adresses:
            with self.subTest():
                response = self.authorized_client.get(url_name[0])
                self.assertTemplateUsed(response, url_name[1])

    def test_post_edit_correct_redirect(self):
        correct_pathes_to_redirect = [
            [self.POST_EDIT_AUTHOR_URL, self.guest_client,
             LOGIN_URL_TESTUSER_URL],
            [self.POST_EDIT_URL, self.authorized_client, self.POST_URL]
        ]
        for url in correct_pathes_to_redirect:
            response = url[1].get(url[0])
            self.assertRedirects(response, url[2])

    def test_authorized_user_can_subscribe_and_unsubscribe(self):
        """Тест на то, что только авторизированный
                пользователь может подписываться"""
        response = self.authorized_client.get(PROFILE_FOLLOW_URL)
        self.assertEqual(response.status_code, 302)
        response = self.authorized_client.get(PROFILE_UNFOLLOW_URL)
        self.assertEqual(response.status_code, 302)
