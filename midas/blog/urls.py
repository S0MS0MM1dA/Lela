from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('post_detail/', views.post_detail),
    path('dashboard/', views.dashboard),
    path('accounts/signin/', views.inkwell_auth),
    
]