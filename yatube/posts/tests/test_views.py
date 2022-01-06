# deals/tests/test_views.py
import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.author = PostPagesTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (reverse(
                'posts:group_list', args=(PostPagesTests.group.slug,))
            ),
            'posts/profile.html': (reverse(
                'posts:profile', args=(PostPagesTests.user.username,))
            ),
            'posts/post_detail.html': (reverse(
                'posts:post_detail', args=(PostPagesTests.post.id,))
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        response = self.authorized_author.get(reverse(
            'posts:post_edit', args=(PostPagesTests.post.id,))
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    # Проверка контекста
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, PostPagesTests.user.username)
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_group_0, PostPagesTests.post.group)
        self.assertEqual(post_image_0, PostPagesTests.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', args=(PostPagesTests.group.slug,))
        )
        response2 = self.authorized_client.get(reverse(
            'posts:group_list', args=(PostPagesTests.group2.slug,))
        )
        first_object = response.context['page_obj'][0]
        first_object2 = response2.context['page_obj'].object_list
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, PostPagesTests.post.author)
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_group_0, PostPagesTests.post.group)
        self.assertEqual(post_image_0, PostPagesTests.post.image)
        self.assertEqual(len(first_object2), 0)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', args=(PostPagesTests.user.username,))
        )
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, PostPagesTests.post.author)
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_group_0, PostPagesTests.post.group)
        self.assertEqual(post_image_0, PostPagesTests.post.image)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', args=(PostPagesTests.post.id,)))
        )
        self.assertEqual(
            response.context.get('post').author, PostPagesTests.post.author
        )
        self.assertEqual(
            response.context.get('post').text, PostPagesTests.post.text
        )
        self.assertEqual(
            response.context.get('post').group, PostPagesTests.post.group
        )
        self.assertEqual(
            response.context.get('post').image, PostPagesTests.post.image
        )
        self.assertEqual(response.context.get(
            'comments')[0].text, PostPagesTests.comment.text
        )
        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, forms.fields.CharField)

    def test_post_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        response2 = self.authorized_author.get(reverse(
            'posts:post_edit', args=(PostPagesTests.post.id,))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response2.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_cache_index_page(self):
        """Проверка работы кэширования на странице index."""
        cache.clear()
        self.post = Post.objects.create(
            author=PostPagesTests.user,
            text='Тестовый пост для проверки кэша',
            group=PostPagesTests.group,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn(self.post.text, response.content.decode('utf-8'))
        Post.objects.latest('id').delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn(self.post.text, response.content.decode('utf-8'))
        page_obj = response.context['page_obj']
        key = make_template_fragment_key('index_page', [page_obj.number])
        cache.delete(key)
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotIn(self.post.text, response.content.decode('utf-8'))

    def test_follow_page_context(self):
        """Шаблон follow_page сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'].object_list
        self.assertEqual(len(first_object), 0)
        Follow.objects.create(
            user=self.user, author=self.author
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_author_0, PostPagesTests.user.username)
        self.assertEqual(post_text_0, PostPagesTests.post.text)
        self.assertEqual(post_group_0, PostPagesTests.post.group)
        self.assertEqual(post_image_0, PostPagesTests.post.image)

    def test_follow_functions(self):
        """Проверка возможности подписаться и отписаться пользователями."""
        follower = 0
        self.guest_client.get(reverse(
            'posts:profile_follow', args=(self.author,))
        )
        self.assertEqual(self.user.follower.count(), follower)
        self.authorized_author.get(reverse(
            'posts:profile_follow', args=(self.author,))
        )
        self.assertEqual(self.user.follower.count(), follower)
        self.authorized_client.get(reverse(
            'posts:profile_follow', args=(self.author,))
        )
        self.assertEqual(self.user.follower.count(), follower + 1)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', args=(self.author,))
        )
        self.assertEqual(self.user.follower.count(), follower)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='user2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.user1,
            text='1 пост',
        )
        cls.paginator = 10  # Количество записей на странице
        cls.post = Post.objects.bulk_create(
            [Post(
                author=cls.user1,
                text=f'Пост {i} пользователя 1',
                group=cls.group) for i in range(1, 14)]
            + [Post(
                author=cls.user2,
                text=f'Пост {i} пользователя 2',
                group=cls.group2) for i in range(1, 14)]
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user1)

    def test_index_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(
            response.context['page_obj']), PaginatorViewsTest.paginator
        )

    def test_index_last_page_contains_records(self):
        response = self.guest_client.get(reverse('posts:index') + '?page=3')
        self.assertEqual(len(
            response.context['page_obj']), (
                Post.objects.count() % PaginatorViewsTest.paginator)
        )

    def test_group_list_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse(
            'posts:group_list', args=(PaginatorViewsTest.group.slug,))
        )
        self.assertEqual(len(
            response.context['page_obj']), PaginatorViewsTest.paginator
        )

    def test_group_list_last_page_contains_records(self):
        response = (self.guest_client.get(reverse('posts:group_list', args=(
            PaginatorViewsTest.group2.slug,)) + '?page=2')
        )
        self.assertEqual(len(response.context['page_obj']), (
            Post.objects.filter(group=PaginatorViewsTest.group2).count()
            % PaginatorViewsTest.paginator)
        )

    def test_profile_first_page_contains_ten_records(self):
        response = (self.guest_client.get(reverse(
            'posts:profile', args=(PaginatorViewsTest.user2.username,)))
        )
        self.assertEqual(len(
            response.context['page_obj']), PaginatorViewsTest.paginator
        )

    def test_profile_last_page_contains_records(self):
        response = (self.guest_client.get(reverse(
            'posts:profile', args=(
                PaginatorViewsTest.user2.username,)) + '?page=2')
        )
        self.assertEqual(len(response.context['page_obj']), (
            Post.objects.filter(author=PaginatorViewsTest.user2).count()
            % PaginatorViewsTest.paginator)
        )
