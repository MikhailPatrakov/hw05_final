from django.contrib.auth import get_user_model
from django.test import TestCase

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        models = {
            PostModelTest.group: PostModelTest.group.title,
            PostModelTest.post: PostModelTest.post.text[:15],
        }
        for model, expected_data in models.items():
            with self.subTest(model=model):
                response = str(model)
                self.assertEqual(response, expected_data)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()

    def test_text_label(self):
        text_label = PostFormTests.form.fields['text'].label
        self.assertTrue(text_label, 'Текст поста')

    def test_group_label(self):
        group_label = PostFormTests.form.fields['group'].label
        self.assertTrue(group_label, 'Группа')

    def test_text_help_text(self):
        text_help_text = PostFormTests.form.fields['text'].help_text
        self.assertTrue(text_help_text, 'Текст нового поста')

    def test_group_help_text(self):
        group_help_text = PostFormTests.form.fields['group'].help_text
        self.assertTrue(group_help_text, 'Группа в которой будет пост')
