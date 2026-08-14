from django.urls import path
from . import views

app_name = 'tags'

urlpatterns = [
    path('', views.index, name='index'),
    path('categories/', views.category_guide, name='category_guide'),
] 