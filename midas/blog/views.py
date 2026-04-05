from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Post, Tag, Category, Comment, Like, Bookmark
from django.http import JsonResponse
from django.db import models

# ── HOME ────────────────────────────────────────────────────
def home(request):
    featured = Post.objects.filter(status='published').first()
    recent   = Post.objects.filter(status='published')[1:7]
    trending = Post.objects.filter(status='published').order_by('-views')[:5]
    tags     = Tag.objects.all()[:12]

    return render(request, 'blog/home.html', {
        'featured': featured,
        'recent':   recent,
        'trending': trending,
        'tags':     tags,
    })


# ── POST DETAIL ─────────────────────────────────────────────
def post_detail(request, slug):
    post     = get_object_or_404(Post, slug=slug, status='published')
    comments = post.comments.filter(parent=None)
    related  = Post.objects.filter(
        tags__in=post.tags.all(), status='published'
    ).exclude(id=post.id).distinct()[:3]

    if related.count() < 3:
        recent_fallback = Post.objects.filter(
            status='published'
        ).exclude(id=post.id).exclude(
            id__in=related.values_list('id', flat=True)
        ).order_by('-created_at')[:3 - related.count()]

    from itertools import chain
    related = list(chain(related, recent_fallback))

    # Count this view
    post.views += 1
    post.save(update_fields=['views'])

    # Has the logged-in user liked / bookmarked this?
    user_liked      = False
    user_bookmarked = False
    if request.user.is_authenticated:
        user_liked      = Like.objects.filter(user=request.user, post=post).exists()
        user_bookmarked = Bookmark.objects.filter(user=request.user, post=post).exists()

    # Handle comment submission (AJAX)
    if request.method == 'POST' and request.user.is_authenticated:
        action = request.POST.get('action')
        if action == 'comment':
            body = request.POST.get('body', '').strip()
            if body:
                comment = Comment.objects.create(
                    post=post,
                    author=request.user,
                    body=body
                )
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success':  True,
                        'username': comment.author.username,
                        'body':     comment.body,
                        'date':     comment.created_at.strftime('%b %d'),
                    })
            return redirect('post_detail', slug=slug)

    # ← THIS WAS MISSING — the actual page render
    return render(request, 'blog/post_detail.html', {
        'post':            post,
        'comments':        comments,
        'related':         related,
        'user_liked':      user_liked,
        'user_bookmarked': user_bookmarked,
    })

# ── EXPLORE ─────────────────────────────────────────────────
def explore(request):
    category_slug = request.GET.get('category')
    tag_slug      = request.GET.get('tag')
    sort          = request.GET.get('sort', 'latest')

    posts = Post.objects.filter(status='published')

    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    if sort == 'trending':
        posts = posts.order_by('-views')
    elif sort == 'most_liked':
        from django.db.models import Count
        posts = posts.annotate(like_cnt=Count('likes')).order_by('-like_cnt')
    else:
        posts = posts.order_by('-created_at')

    posts = posts.distinct()

    categories = Category.objects.all()
    tags       = Tag.objects.all()

    return render(request, 'blog/explore.html', {
        'posts':           posts,
        'categories':      categories,
        'tags':            tags,
        'active_category': category_slug,
        'active_tag':      tag_slug,
        'sort':            sort,
    })

# ── TAGS PAGE ─────────────────────────────────────────────
def tags_page(request):
    from django.db.models import Count
    tags = Tag.objects.annotate(
        post_count=Count('posts', filter=models.Q(posts__status='published'))
    ).order_by('-post_count')

    return render(request, 'blog/tags.html', {'tags': tags})

# ── SIGNUP ───────────────────────────────────────────────────
def signup(request):
    if request.method == 'POST':
        username   = request.POST['username']
        email      = request.POST['email']
        password1  = request.POST['password1']
        password2  = request.POST['password2']

        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('signup')

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        login(request, user)
        messages.success(request, f'Welcome to Lela, {username}!')
        return redirect('home')

    return render(request, 'accounts/signup.html')


# ── SIGNIN ───────────────────────────────────────────────────
def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user     = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('signin')

    return render(request, 'accounts/signin.html')


# ── SIGNOUT ──────────────────────────────────────────────────
def signout(request):
    logout(request)
    return redirect('home')


# ── POST CREATE ──────────────────────────────────────────────
@login_required
def post_create(request):
    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        body     = request.POST.get('body', '').strip()
        status   = request.POST.get('status', 'draft')
        cat_id   = request.POST.get('category')
        tag_ids  = request.POST.getlist('tags')
        cover    = request.FILES.get('cover_image')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect('post_create')

        post = Post.objects.create(
            title=title,
            body=body,
            author=request.user,
            status=status,
            cover_image=cover if cover else None,
        )

        if cat_id:
            try:
                post.category = Category.objects.get(id=cat_id)
            except Category.DoesNotExist:
                pass

        if tag_ids:
            post.tags.set(Tag.objects.filter(id__in=tag_ids))

        post.save()

        if status == 'published':
            messages.success(request, 'Post published successfully.')
            return redirect('post_detail', slug=post.slug)
        else:
            messages.success(request, 'Draft saved.')
            return redirect('dashboard_drafts')

    categories = Category.objects.all()
    tags       = Tag.objects.all()
    return render(request, 'blog/post_form.html', {
        'categories': categories,
        'tags':       tags,
        'mode':       'create',
    })

# ── POST EDIT ────────────────────────────────────────────────
@login_required
def post_edit(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)

    if request.method == 'POST':
        title   = request.POST.get('title', '').strip()
        body    = request.POST.get('body', '').strip()
        status  = request.POST.get('status', 'draft')
        cat_id  = request.POST.get('category')
        tag_ids = request.POST.getlist('tags')
        cover   = request.FILES.get('cover_image')

        if not title:
            messages.error(request, 'Title is required.')
            return redirect('post_edit', slug=slug)

        post.title  = title
        post.body   = body
        post.status = status
        if cover:
            post.cover_image = cover

        if cat_id:
            try:
                post.category = Category.objects.get(id=cat_id)
            except Category.DoesNotExist:
                pass

        post.tags.set(Tag.objects.filter(id__in=tag_ids))
        post.save()

        if status == 'published':
            messages.success(request, 'Post updated and published.')
            return redirect('post_detail', slug=post.slug)
        else:
            messages.success(request, 'Draft saved.')
            return redirect('dashboard_drafts')

    categories = Category.objects.all()
    tags       = Tag.objects.all()
    return render(request, 'blog/post_form.html', {
        'post':        post,
        'categories':  categories,
        'tags':        tags,
        'mode':        'edit',
        'post_tags':   list(post.tags.values_list('id', flat=True)),
    })


# ── DASHBOARD ────────────────────────────────────────────────
@login_required
def dashboard(request):
    posts = Post.objects.filter(
        author=request.user, status='published'
    ).order_by('-created_at')
    drafts_count = Post.objects.filter(
        author=request.user, status='draft'
    ).count()
    return render(request, 'dashboard/my_posts.html', {
        'posts':        posts,
        'drafts_count': drafts_count,
        'active_tab':   'my_posts',
    })


@login_required
def dashboard_drafts(request):
    drafts = Post.objects.filter(
        author=request.user, status='draft'
    ).order_by('-updated_at')
    drafts_count = drafts.count()
    return render(request, 'dashboard/drafts.html', {
        'drafts':       drafts,
        'drafts_count': drafts_count,
        'active_tab':   'drafts',
    })


@login_required
def dashboard_bookmarks(request):
    bookmarks = Bookmark.objects.filter(
        user=request.user
    ).select_related('post').order_by('-created_at')
    drafts_count = Post.objects.filter(
        author=request.user, status='draft'
    ).count()
    return render(request, 'dashboard/bookmarks.html', {
        'bookmarks':    bookmarks,
        'drafts_count': drafts_count,
        'active_tab':   'bookmarks',
    })


@login_required
def dashboard_settings(request):
    drafts_count = Post.objects.filter(
        author=request.user, status='draft'
    ).count()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            request.user.first_name = request.POST.get('name', '').strip()
            request.user.bio        = request.POST.get('bio', '').strip()
            request.user.website    = request.POST.get('website', '').strip()
            if 'avatar' in request.FILES:
                request.user.avatar = request.FILES['avatar']
            request.user.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('dashboard_settings')

        if action == 'change_password':
            old  = request.POST.get('old_password')
            new1 = request.POST.get('new_password1')
            new2 = request.POST.get('new_password2')
            if not request.user.check_password(old):
                messages.error(request, 'Current password is incorrect.')
            elif new1 != new2:
                messages.error(request, 'New passwords do not match.')
            elif len(new1) < 8:
                messages.error(request, 'Password must be at least 8 characters.')
            else:
                request.user.set_password(new1)
                request.user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password updated successfully.')
            return redirect('dashboard_settings')

    return render(request, 'dashboard/settings.html', {
        'drafts_count': drafts_count,
        'active_tab':   'settings',
    })


@login_required
def toggle_publish(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)
    post.status = 'draft' if post.status == 'published' else 'published'
    post.save(update_fields=['status'])
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'status': post.status})
    return redirect('dashboard')


@login_required
def delete_post(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)
    post.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('dashboard')

@login_required
def toggle_like(request, slug):
    post    = get_object_or_404(Post, slug=slug)
    liked   = False
    like    = Like.objects.filter(user=request.user, post=post).first()

    if like:
        like.delete()
    else:
        Like.objects.create(user=request.user, post=post)
        liked = True

    return JsonResponse({
        'success': True,
        'liked':   liked,
        'count':   post.like_count(),
    })


@login_required
def toggle_bookmark(request, slug):
    post       = get_object_or_404(Post, slug=slug)
    bookmarked = False
    bookmark   = Bookmark.objects.filter(user=request.user, post=post).first()

    if bookmark:
        bookmark.delete()
    else:
        Bookmark.objects.create(user=request.user, post=post)
        bookmarked = True

    return JsonResponse({
        'success':    True,
        'bookmarked': bookmarked,
    })

def search(request):
    query   = request.GET.get('q', '').strip()
    results = Post.objects.none()

    if query:
        results = Post.objects.filter(
            Q(title__icontains=query) |
            Q(body__icontains=query)  |
            Q(tags__name__icontains=query),
            status='published'
        ).distinct().order_by('-created_at')

    return render(request, 'blog/search.html', {
        'query':   query,
        'results': results,
    })