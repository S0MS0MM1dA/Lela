from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
import re


# ── 1. CUSTOM USER ──────────────────────────────────────────
class User(AbstractUser):
    bio       = models.TextField(blank=True)
    avatar    = models.ImageField(upload_to='avatars/', blank=True, null=True)
    website   = models.URLField(blank=True)
    followers = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='following',
        blank=True
    )

    def follower_count(self):
        return self.followers.count()

    def following_count(self):
        return self.following.count()

    def __str__(self):
        return self.username


# ── 2. CATEGORY ─────────────────────────────────────────────
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


# ── 3. TAG ───────────────────────────────────────────────────
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ── 4. POST ──────────────────────────────────────────────────
class Post(models.Model):

    STATUS_CHOICES = [
        ('draft',     'Draft'),
        ('published', 'Published'),
    ]

    title       = models.CharField(max_length=300)
    slug        = models.SlugField(unique=True, blank=True, max_length=320)
    body        = models.TextField()          # stores Quill HTML
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True)
    excerpt     = models.TextField(max_length=300, blank=True)

    author      = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    category    = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='posts'
    )
    tags        = models.ManyToManyField(Tag, blank=True, related_name='posts')

    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    views       = models.PositiveIntegerField(default=0)
    read_time   = models.PositiveIntegerField(default=1)  # minutes

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Post.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug

        # Auto-calculate read time (avg 200 words/min)
        clean = re.sub(r'<[^>]+>', '', self.body)   # strip HTML tags
        word_count = len(clean.split())
        self.read_time = max(1, word_count // 200)

        # Auto-generate excerpt if empty
        if not self.excerpt:
            self.excerpt = clean[:250].strip()

        super().save(*args, **kwargs)

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.filter(parent=None).count()

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']


# ── 5. COMMENT ───────────────────────────────────────────────
class Comment(models.Model):
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    body       = models.TextField()
    parent     = models.ForeignKey(          # None = top-level, set = reply
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'

    class Meta:
        ordering = ['created_at']


# ── 6. LIKE ──────────────────────────────────────────────────
class Like(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')   # one like per user per post

    def __str__(self):
        return f'{self.user.username} liked {self.post.title}'


# ── 7. BOOKMARK ──────────────────────────────────────────────
class Bookmark(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post       = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')   # one bookmark per user per post

    def __str__(self):
        return f'{self.user.username} bookmarked {self.post.title}'