from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Post, Tag, Category, Comment, Like, Bookmark
from django.http import JsonResponse

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
        messages.success(request, f'Welcome to Inkwell, {username}!')
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
        title  = request.POST['title']
        body   = request.POST['body']
        status = request.POST.get('status', 'draft')

        post = Post.objects.create(
            title=title,
            body=body,
            author=request.user,
            status=status,
        )
        return redirect('post_detail', slug=post.slug)

    categories = Category.objects.all()
    tags       = Tag.objects.all()
    return render(request, 'blog/post_form.html', {
        'categories': categories,
        'tags':       tags,
    })


# ── POST EDIT ────────────────────────────────────────────────
@login_required
def post_edit(request, slug):
    post = get_object_or_404(Post, slug=slug, author=request.user)

    if request.method == 'POST':
        post.title  = request.POST['title']
        post.body   = request.POST['body']
        post.status = request.POST.get('status', 'draft')
        post.save()
        return redirect('post_detail', slug=post.slug)

    categories = Category.objects.all()
    tags       = Tag.objects.all()
    return render(request, 'blog/post_form.html', {
        'post':       post,
        'categories': categories,
        'tags':       tags,
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