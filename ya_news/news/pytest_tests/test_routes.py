from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects

from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name', ('news:home', 'users:login', 'users:logout', 'users:signup')
)
def test_home_page_access_for_anon(client, name):
    """
    Главная страница доступна анонимному пользователю.
    Страницы регистрации пользователей,
    входа в учётную запись и выхода из неё доступны анонимным пользователям.
    """
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
def test_news_page_access_for_anon(client, news):
    """Страница отдельной новости доступна анонимному пользователю."""
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (pytest.lazy_fixture('admin_client'),  # type: ignore
         HTTPStatus.NOT_FOUND),
        (pytest.lazy_fixture('author_client'), HTTPStatus.OK),  # type: ignore
    ),
)
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_comment_edit_delete_access_for_author(
    parametrized_client, expected_status, name, comment
):
    """
    Страницы удаления и редактирования комментария доступны автору комментария.
    Авторизованный пользователь не может зайти на страницы редактирования или
    удаления чужих комментариев (возвращается ошибка 404).
    """
    url = reverse(name, kwargs={'pk': comment.pk})
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name',
    ('news:edit', 'news:delete'),
)
def test_anon_redirect_to_login_on_edit_delete_attempt(client, name, comment):
    """
    При попытке перейти на страницу редактирования или удаления комментария
    анонимный пользователь перенаправляется на страницу авторизации.
    """
    login_url = reverse('users:login')
    url = reverse(name, kwargs={'pk': comment.pk})
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
