from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_pavel = User.objects.create_user(username='pavel')
        cls.group = Group.objects.create(
            title='testgroup', description='testdesc', slug='testslug')
        cls.post_pavel = Post.objects.create(
            text='Тестовый супер текст',
            author=User.objects.get(username=cls.author_pavel.username),
            group=Group.objects.get(slug=cls.group.slug),
        )
        cls.author_testuser = User.objects.create_user(username='TestUser')
        cls.post_testuser = Post.objects.create(
            text='Тестовый супер текст2',
            author=User.objects.get(username=cls.author_testuser.username),
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username=self.author_testuser.username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.test_addresses = [
            reverse('index'),
            reverse('group', kwargs={'slug': self.group.slug}),
            reverse('new_post'),
            reverse('profile', kwargs={
                'username': self.author_pavel.username}),
            reverse('post', kwargs={'username': self.author_pavel.username,
                                    'post_id': self.post_pavel.id}),
            reverse('post_edit', kwargs={
                                    'username': self.author_pavel.username,
                                    'post_id': self.post_pavel.id}
                    )
        ]

    def test_for_all_users_except_post_edit(self):
        """Тест status_code для всех страниц кроме post_edit"""
        addresses = {
            self.test_addresses[0]: 200,
            self.test_addresses[1]: 200,
            self.test_addresses[3]: 200,
            self.test_addresses[4]: 200,
            self.test_addresses[5]: 302,
        }
        for address, expected_status_code in addresses.items():
            with self.subTest(value=address):
                current_status_code = \
                    self.authorized_client.get(address).status_code
                self.assertEqual(current_status_code, expected_status_code)

                current_status_code = \
                    self.guest_client.get(address).status_code
                self.assertEqual(current_status_code, expected_status_code)

    def test_for_post_edit(self):
        """Тест status_code для post_edit"""

        status_code = self.authorized_client.get(self.test_addresses[2]) \
            .status_code
        self.assertEqual(status_code, 200)

        status_code_unauthorized = self.guest_client.get(
            self.test_addresses[2]).status_code
        self.assertEqual(status_code_unauthorized, 302)

    def test_profile_post_edit_by_creator(self):
        """Проверка доступности адреса '/<username>/<post_id>/edit/'
        для авторизированного пользователя(автора поста)."""
        response = self.authorized_client.get(
            reverse('post_edit',
                    kwargs={'username': self.author_testuser.username,
                            'post_id': self.post_testuser.id}))
        self.assertEqual(response.status_code, 200)

    def test_urls_correct_templates(self):
        """Проверка шаблона для адреса '/', '/group/testslug/', '/new'."""
        templates_correct = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={'slug': self.group.slug}),
            'new_post.html': reverse('new_post')
        }

        for template, url_name in templates_correct.items():
            with self.subTest():
                response = self.authorized_client.get(url_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_correct_template(self):
        # Я пытался создать список в templates_correct для этого теста,
        # но каждый раз натыкался на проблему
        # 'No templates used to render the response', не смог ее решить:(
        """Проверка шаблона для адреса '/<username>/<post_id>/edit/'"""
        response = self.authorized_client.get(
            reverse('post_edit',
                    kwargs={'username': self.author_testuser.username,
                            'post_id': self.post_testuser.id}))
        self.assertTemplateUsed(response, 'new_post.html')

    def test_post_edit_correct_redirect_unauthorized(self):
        """Проверка редиректа для адреса '/<username>/<post_id>/edit/',
         для неавторизированного пользователя"""
        response = self.guest_client.get(
            reverse('post_edit',
                    kwargs={'username': self.author_testuser.username,
                            'post_id': self.post_testuser.id}), follow=True)
        self.assertRedirects(response, '/auth/login/?next=/TestUser/2/edit/')

    def test_post_edit_correct_redirect_authorized_not_author(self):
        """Проверка редиректа для адреса '/<username>/<post_id>/edit/',
         для авторизированного пользователя(не автора)"""
        response = self.authorized_client.get(
            reverse('post_edit',
                    kwargs={'username': self.author_pavel.username,
                            'post_id': self.post_pavel.id}), follow=True)
        self.assertRedirects(response, '/pavel/1/')

    def test_404_error_when_page_doesnt_exist(self):
        """Проверка что если пользователь перейдет на несуществующую страницу,
         то сервер возвратит код 404"""
        response = self.authorized_client.get('/not/existing/page')
        self.assertEqual(response.status_code, 404)

    def test_authorized_user_can_comment_posts(self):
        """Тест на то, что только авторизирвоанный
        пользователь может комментировать посты"""
        response = self.authorized_client.get(reverse('add_comment', kwargs={
            'username': self.post_pavel.author.username,
            'post_id': self.post_pavel.id}))
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_user_cant_comment_posts(self):
        """Тест на то, что только авторизированный
        пользователь может комментировать посты"""
        response = self.guest_client.get(reverse('add_comment', kwargs={
            'username': self.post_pavel.author.username,
            'post_id': self.post_pavel.id}))
        self.assertEqual(response.status_code, 302)

    def test_authorized_user_can_subscribe_and_unsubscribe(self):
        """Тест на то, что только авторизированный
                пользователь может подписываться"""
        response = self.authorized_client.get(
            reverse('profile_follow', kwargs={
                'username': self.author_testuser.username}))
        self.assertEqual(response.status_code, 302)
        response = self.authorized_client.get(
            reverse('profile_unfollow',
                    kwargs={'username': self.author_testuser.username}))
        self.assertEqual(response.status_code, 302)
