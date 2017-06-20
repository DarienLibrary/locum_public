"""locum URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework import routers

from patron.views import PatronViewSet, CheckoutViewSet
from harvest.views import WorkRecordViewSet, BibliographicRecordViewSet
from ratings.views import WishViewSet, RatingViewSet, ReviewViewSet
from tags.views import TagViewSet, LabelViewSet


router = routers.DefaultRouter()
router.register(r'patrons', PatronViewSet)
router.register(r'checkouts', CheckoutViewSet, base_name='checkouts')
router.register(r'works', WorkRecordViewSet)
router.register(r'bibs', BibliographicRecordViewSet)
router.register(r'wishes', WishViewSet)
router.register(r'ratings', RatingViewSet)
router.register(r'reviews', ReviewViewSet)
router.register(r'tags', TagViewSet)
router.register(r'labels', LabelViewSet)

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/', include('search.urls', namespace="search")),
]

urlpatterns += router.urls
