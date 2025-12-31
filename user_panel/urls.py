from django.urls import path
from . import views

app_name = 'user_panel'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('main/<int:user_id>/', views.locations_map, name='locations_map'),
]
