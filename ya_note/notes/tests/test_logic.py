from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


URL_N_SUC = 'notes:success'
URL_N_ADD = 'notes:add'
URL_N_EDIT = 'notes:edit'
URL_N_DEL = 'notes:delete'


User = get_user_model()


class TestLogic(TestCase):
    """Класс TestLogic предназначен для тестирования логики"""

    NEW_TITLE = 'Новый заголовок'
    TEST_TEXT = 'Тестовый текст'
    TITLE = 'Заголовок'
    TEXT = 'Текст'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.author_user = User.objects.create(username='Автор пользователь')
        cls.data = {
            'slug': 'slug',
            'title': cls.NEW_TITLE,
            'text': cls.TEST_TEXT,
        }

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.author_user_client = Client()
        self.author_user_client.force_login(self.author_user)
        super().setUp()
        self.note = None

    def test_logged_in_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        initial_count = Note.objects.count()
        url = reverse('notes:add')
        response = self.user_client.post(url, data=self.data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), initial_count + 1)
        note = Note.objects.last()
        self.assertEqual(note.slug, self.data['slug'])
        self.assertEqual(note.title, self.data['title'])
        self.assertEqual(note.text, self.data['text'])
        self.assertEqual(note.author, self.user)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        initial_count = Note.objects.count()
        url = reverse('notes:add')
        response = self.client.post(url, self.data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), initial_count)

    def test_not_create_two_note(self):
        """Невозможно создать две заметки с одинаковым slug."""
        initial_count = Note.objects.count()
        self.note = Note.objects.create(
            author=self.user,
            title=self.TITLE,
            text=self.TEXT,
        )
        url = reverse('notes:add')
        response = self.user_client.post(
            url,
            data={
                'slug': self.note.slug,
                'title': self.NEW_TITLE,
                'text': self.TEST_TEXT,
            },
        )
        self.assertFormError(
            response, 'form', 'slug', errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), initial_count + 1)

    def test_slug_auto_filled_by_pytils_if_empty(self):
        """
        Если при создании заметки не заполнен slug,
        то он формируется автоматически,
        с помощью функции pytils.translit.slugify.
        """
        url = reverse('notes:add')
        self.data.pop('slug')
        response = self.user_client.post(url, data=self.data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        note = Note.objects.get()
        expected_slug = slugify(self.data['title'])
        self.assertEqual(note.slug, expected_slug)

    def test_user_can_edit_note(self):
        """Пользователь может редактировать свои заметки."""
        self.note = Note.objects.create(
            author=self.user,
            title=self.TITLE,
            text=self.TEXT,
        )
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.user_client.post(url, self.data)
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.slug, self.data['slug'])
        self.assertEqual(self.note.title, self.data['title'])
        self.assertEqual(self.note.text, self.data['text'])

    def test_user_can_edit_others_note(self):
        """Пользователь не может редактировать чужие заметки."""
        self.note = Note.objects.create(
            author=self.user,
            title=self.TITLE,
            text=self.TEXT,
        )
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_user_client.post(url, self.data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertNotEqual(self.note.slug, self.data['slug'])
        self.assertNotEqual(self.note.title, self.data['title'])
        self.assertNotEqual(self.note.text, self.data['text'])

    def test_user_can_delete_note(self):
        """Пользователь может удалять свои заметки."""
        initial_count = Note.objects.count()
        self.note = Note.objects.create(
            author=self.user,
            title=self.TITLE,
            text=self.TEXT,
        )
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.user_client.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), initial_count)

    def test_user_can_delete_others_note(self):
        """Пользователь не может удалять чужие заметки."""
        initial_count = Note.objects.count()
        self.note = Note.objects.create(
            author=self.user,
            title=self.TITLE,
            text=self.TEXT,
        )
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_user_client.post(url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), initial_count + 1)
