from django.conf.urls import url

from . import views

app_name = 'contests'
urlpatterns = [
    url(r'^$', views.list),
    url(r'^setup$', views.ContestCreate.as_view(), name='setup_new'),
    url(r'^(?P<contests_code>[-\w]+)/$', views.description,
        name='description'),
]
