from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


CORRECT_DATA_FORM = {'text': 'Новый текст комментария'}


@pytest.mark.django_db
def test_no_anon_comment(client, news):
    """Анонимный пользователь не может отправить комментарий."""
    url = reverse('news:detail', args=(news.id,))
    count_comments_before = Comment.objects.count()
    client.post(url, data=CORRECT_DATA_FORM)
    assert count_comments_before == Comment.objects.count()


@pytest.mark.django_db
def test_author_user_comment(author, author_client, news):
    """Авторизованный пользователь может отправить комментарий."""
    new_comment_text = {'text': 'Новый текст'}
    count_comments_before = Comment.objects.count()
    url = reverse('news:detail', kwargs={'pk': news.pk})
    author_client.post(url, data=new_comment_text)
    assert count_comments_before + 1 == Comment.objects.count()
    comment = Comment.objects.get()
    assert comment.text == new_comment_text['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_comment_with_banned_words_fails(reader_client, news):
    """
    Если комментарий содержит запрещённые слова, он не будет опубликован,
    а форма вернёт ошибку.
    """
    url = reverse('news:detail', args=(news.id,))
    count_comments_before = Comment.objects.count()
    clean_text_data = {
        'text': f'Тестовый текст, {BAD_WORDS[0]}, последующий текст'}
    response = reader_client.post(url, data=clean_text_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    assert count_comments_before == Comment.objects.count()


@pytest.mark.django_db
def test_author_user_edit_comment(author_client, news, comment):
    """Авторизованный пользователь может редактировать свои комментарии."""
    new_comment_text = {'text': 'Новый текст'}
    news_url = reverse('news:detail', kwargs={'pk': news.pk})
    comment_url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = author_client.post(comment_url, data=new_comment_text)
    assertRedirects(response, news_url + '#comments')
    comment.refresh_from_db()
    assert comment.text == new_comment_text['text']


@pytest.mark.django_db
def test_author_user_cannot_edit_comment(admin_client, comment):
    """Авторизованный пользователь не может редактировать чужие комментарии."""
    new_comment_text = {'text': 'Новый текст'}
    comment_url = reverse('news:edit', kwargs={'pk': comment.pk})
    response = admin_client.post(comment_url, data=new_comment_text)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == 'Текст комментария'


@pytest.mark.django_db
def test_author_user_delete_comment(author_client, news, comment):
    """Авторизованный пользователь может удалять свои комментарии."""
    count_comments_before = Comment.objects.count()
    news_url = reverse('news:detail', kwargs={'pk': news.pk})
    comment_url = reverse('news:delete', kwargs={'pk': comment.pk})
    response = author_client.delete(comment_url)
    assertRedirects(response, news_url + '#comments')
    assert count_comments_before - 1 == Comment.objects.count()


@pytest.mark.django_db
def test_author_user_cannot_delete_comment(admin_client, comment):
    """Авторизованный пользователь не может удалять чужие комментарии."""
    count_comments_before = Comment.objects.count()
    comment_url = reverse('news:delete', kwargs={'pk': comment.pk})
    response = admin_client.delete(comment_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert count_comments_before == Comment.objects.count()
