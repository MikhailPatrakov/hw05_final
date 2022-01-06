from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.author = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_urls_exists_at_desired_location(self):
        """Страницы по URL-адресам доступны неавторизованному пользователю."""
        url_names = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{PostURLTests.user.username}/': HTTPStatus.OK,
            f'/posts/{PostURLTests.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for adress, expected_response in url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, expected_response)

    def test_url_redirect_anonymous_on_admin_login(self):
        """Страница перенаправит анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{PostURLTests.post.id}/edit/'
        )

    def test_url_redirect_not_author(self):
        """Страница /posts/post_id/edit/ перенаправит пользователя,
        не являющимся автором поста на страницу c описанием поста."""
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/posts/{PostURLTests.post.id}/'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names_1 = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
        }
        templates_url_names_2 = {
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for adress, template in templates_url_names_1.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
        for adress, template in templates_url_names_2.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
        response = self.authorized_author.get(
            f'/posts/{PostURLTests.post.id}/edit/'
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')
