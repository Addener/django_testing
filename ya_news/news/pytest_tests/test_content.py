import pytest

from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm


@pytest.mark.django_db
def test_max_10_news_on_homepage(client, list_news):
    """Количество новостей на главной странице — не более 10."""
    url = reverse('news:home')
    response = client.get(url)
    news_count = response.context['object_list'].count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_sorted_by_freshness(client, list_news):
    """
    Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    any_news = [test_news for test_news in object_list]
    sorted_news = sorted(any_news, key=lambda x: x.date, reverse=True)
    assert sorted_news == list_news


@pytest.mark.django_db
def test_comments_sorted_chronologically(client, news, list_comments):
    """
    Комментарии на странице отдельной новости отсортированы в
    хронологическом порядке: старые в начале списка, новые — в конце.
    """
    url = reverse('news:detail', kwargs={'pk': news.pk})
    response = client.get(url)
    assert 'news' in response.context
    list_comments = response.context['news'].comment_set.all()
    comments_dates = [comment.created for comment in list_comments]
    sorted_comments = sorted(comments_dates)
    assert comments_dates == sorted_comments


@pytest.mark.django_db
def test_anonymous_hasnt_form_comment(client, news):
    """Проверка наличия формы комментария для анонима на стр. новости."""
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_user_has_form_comment(reader_client, news):
    """Проверка наличия формы комментария для пользователя на стр. новости."""
    url = reverse('news:detail', args=(news.id,))
    response = reader_client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
