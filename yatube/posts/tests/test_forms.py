import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
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
            text='Первый тестовый текст',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.posts_count = Post.objects.count()
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
        self.form_data = {
            'text': 'Тестовый текст',
            'group': PostFormTests.group.id,
            'image': uploaded,
        }

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', args=(PostFormTests.user.username,))
        )
        self.assertEqual(Post.objects.count(), self.posts_count + 1)
        img_name = Post.image.field.upload_to + self.form_data['image'].name
        self.assertTrue(
            Post.objects.filter(
                text=self.form_data['text'],
                group=self.form_data['group'],
                image=img_name
            ).exists()
        )
        new_post = Post.objects.latest('id')
        self.assertEqual(PostFormTests.user, new_post.author)
        self.assertEqual(self.form_data['text'], new_post.text)
        self.assertEqual(self.form_data['group'], new_post.group.id)
        self.assertEqual(img_name, new_post.image.name)

    def test_edit_post(self):
        """Валидная форма редактируется Post."""
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=(PostFormTests.post.id,)),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(PostFormTests.post.id,))
        )
        self.assertEqual(Post.objects.count(), self.posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=self.form_data['text'],
                group=self.form_data['group']
            ).exists()
        )

    def test_cant_post_create_unauthorized_client(self):
        """Проверка отсутствия возможности создания поста
        неавторизованным пользователем"""
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse(
                'users:login') + '?next=' + reverse('posts:post_create')
        )
        self.assertEqual(Post.objects.count(), self.posts_count)

    def test_create_comment(self):
        """Валидная форма создает запись в Comment."""
        form_comment = {
            'text': 'Текст комментария'
        }
        comments_count = self.post.comments.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(PostFormTests.post.id,)),
            data=form_comment,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(PostFormTests.post.id,))
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=form_comment['text']
            ).exists()
        )
        new_comment = Comment.objects.latest('id')
        self.assertEqual(PostFormTests.user, new_comment.author)
        self.assertEqual(form_comment['text'], new_comment.text)

    def test_cant_comment_create_unauthorized_client(self):
        """Проверка отсутствия возможности создания комментария
        неавторизованным пользователем"""
        form_comment = {
            'text': 'Текст комментария'
        }
        comments_count = self.post.comments.count()
        response = self.guest_client.post(
            reverse('posts:add_comment', args=(PostFormTests.post.id,)),
            data=form_comment,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('users:login') + '?next=' + reverse(
                'posts:add_comment', args=(PostFormTests.post.id,))
        )
        self.assertEqual(Comment.objects.count(), comments_count)
