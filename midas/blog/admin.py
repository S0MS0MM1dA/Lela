from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Post, Tag, Category, Comment, Like, Bookmark

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display        = ['title', 'author', 'status', 'views', 'read_time', 'created_at']
    list_filter         = ['status', 'category', 'created_at']
    search_fields       = ['title', 'body', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy      = 'created_at'
    ordering            = ['-created_at']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display        = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display  = ['author', 'post', 'created_at', 'parent']
    search_fields = ['body', 'author__username']
    list_filter   = ['created_at']

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']

@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']

admin.site.register(User, UserAdmin)