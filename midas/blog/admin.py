from django.contrib import admin

# Register your models here.

from django.contrib.auth.admin import UserAdmin
from .models import User, Post, Tag, Category, Comment, Like, Bookmark

admin.site.register(User, UserAdmin)
admin.site.register(Post)
admin.site.register(Tag)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Bookmark)