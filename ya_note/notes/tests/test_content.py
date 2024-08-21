from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm


URL_N_LIST = 'notes:list'
URL_N_ADD = 'notes:add'
URL_N_EDIT = 'notes:edit'


User = get_user_model()


class TestContent(TestCase):
    """Класс TestContent предназначен для тестирования контента"""

    TITLE = 'Заголовок'
    TEXT = 'Текст'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.author_user = User.objects.create(username='Автор пользователь')
        cls.note = Note.objects.create(
            author=cls.user,
            title=cls.TITLE,
            text=cls.TEXT,
        )

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.author_user_client = Client()
        self.author_user_client.force_login(self.author_user)

    def test_note_passed_to_page_in_object_list(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок в списке
        object_list в словаре context.
        В список заметок одного пользователя не попадают заметки другого
        пользователя.
        """
        users_statuses = (
            (self.user_client, True),
            (self.author_user_client, False),
        )
        for user, note_list in users_statuses:
            with self.subTest(user=user):
                url = reverse(URL_N_LIST)
                response = user.get(url)
                object_list = response.context['object_list']
                self.assertIs((self.note in object_list), note_list)

    def test_forms_passed_to_create_and_edit_pages(self):
        """На страницы создания и редактирования заметки передаются формы."""
        urls = (
            (URL_N_ADD, None),
            (URL_N_EDIT, (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.user_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
