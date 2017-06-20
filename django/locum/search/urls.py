from django.conf.urls import url, include

from . import views


urlpatterns = [
    url(r'^booklist/$', views.BookListView.as_view(), name="booklist"),
    url(r'^$', views.SearchView.as_view(), name='search'),
]
