from django.urls import path
from . import views

app_name = 'mapper'
urlpatterns = [
    path('', views.index, name='index'),
    path('index_node_map/', views.index_node_map, name='index_node_map'),
    path('search/', views.search, name='search'),
    path('node_map/', views.node_map, name='node_map'),
    path('results_report/', views.results_report, name='results_report'),
    path('contact/', views.contact, name='contact'),
    path('acknowledgements/', views.acknowledgements, name='acknowledgements'),
    path('about/', views.about, name='about')
]
