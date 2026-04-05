from django.urls import path

from blog import api_views
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('explore/', views.explore, name='explore'),
    path('tags/', views.tags_page, name='tags_page'),

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
    path('dashboard/delete/<slug:slug>/', views.delete_post, name='delete_post'),

    # Post interactions
    path('post/like/<slug:slug>/',     views.toggle_like,     name='toggle_like'),
    path('post/bookmark/<slug:slug>/', views.toggle_bookmark, name='toggle_bookmark'),

    # Search
    path('search/', views.search, name='search'),


    # ── REST API
    path('api/posts/', api_views.post_list, name='api_post_list'),
    path('api/posts/<slug:slug>/', api_views.post_detail, name='api_post_detail'),
    path('api/posts/<slug:slug>/comments/', api_views.post_comments, name='api_post_comments'),
    path('api/posts/<slug:slug>/like/', api_views.post_like, name='api_post_like'),
    path('api/posts/<slug:slug>/bookmark/', api_views.post_bookmark, name='api_post_bookmark'),
    path('api/tags/', api_views.tag_list, name='api_tag_list'),
    path('api/categories/', api_views.category_list, name='api_category_list'),
    path('api/users/<str:username>/', api_views.user_profile, name='api_user_profile'),
    path('api/trending/', api_views.trending_posts, name='api_trending'),
    path('api/search/', api_views.search_posts, name='api_search'),
]