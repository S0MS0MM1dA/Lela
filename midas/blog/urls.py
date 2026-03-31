from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),

    # Auth
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),

    # Write / Edit
    path('write/', views.post_create, name='post_create'),
    path('edit/<slug:slug>/', views.post_edit, name='post_edit'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/drafts/', views.dashboard_drafts, name='dashboard_drafts'),
    path('dashboard/bookmarks/', views.dashboard_bookmarks, name='dashboard_bookmarks'),
    path('dashboard/settings/', views.dashboard_settings, name='dashboard_settings'),
    path('dashboard/toggle/<slug:slug>/', views.toggle_publish, name='toggle_publish'),

    # Post interactions
    path('post/like/<slug:slug>/',     views.toggle_like,     name='toggle_like'),
    path('post/bookmark/<slug:slug>/', views.toggle_bookmark, name='toggle_bookmark'),

    # Search
    path('search/', views.search, name='search'),
]