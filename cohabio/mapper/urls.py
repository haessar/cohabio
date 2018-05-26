from django.urls import path
from . import views

app_name = 'mapper'
urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search, name='search'),
    path('contact/', views.contact, name='contact'),
    path('acknowledgements/', views.acknowledgements, name='acknowledgements'),
    path('about/', views.about, name='about')
]
