from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Post, Tag, Category, Comment, Like, Bookmark, User
from .serializers import (
    PostListSerializer, PostDetailSerializer,
    PostCreateSerializer, CommentSerializer,
    TagSerializer, CategorySerializer, AuthorSerializer
)


# ── GET /api/posts/
# ── POST /api/posts/
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_list(request):

    if request.method == 'GET':
        posts = Post.objects.filter(status='published').order_by('-created_at')

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            posts = posts.filter(tags__slug=tag)

        # Filter by category
        category = request.GET.get('category')
        if category:
            posts = posts.filter(category__slug=category)

        # Search
        q = request.GET.get('search')
        if q:
            posts = posts.filter(
                Q(title__icontains=q) |
                Q(body__icontains=q)  |
                Q(tags__name__icontains=q)
            ).distinct()

        # Paginate
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(posts, request)
        serializer = PostListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    if request.method == 'POST':
        serializer = PostCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── GET /api/posts/<slug>/
# ── PUT /api/posts/<slug>/
# ── DELETE /api/posts/<slug>/
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, status='published')

    if request.method == 'GET':
        # Count view
        post.views += 1
        post.save(update_fields=['views'])
        serializer = PostDetailSerializer(post, context={'request': request})
        return Response(serializer.data)

    if request.method == 'PUT':
        if post.author != request.user:
            return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = PostCreateSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        if post.author != request.user:
            return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── GET /api/posts/<slug>/comments/
# ── POST /api/posts/<slug>/comments/
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticatedOrReadOnly])
def post_comments(request, slug):
    post = get_object_or_404(Post, slug=slug, status='published')

    if request.method == 'GET':
        comments   = post.comments.filter(parent=None)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        body = request.data.get('body', '').strip()
        if not body:
            return Response({'error': 'Body is required.'}, status=status.HTTP_400_BAD_REQUEST)
        comment    = Comment.objects.create(post=post, author=request.user, body=body)
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ── POST /api/posts/<slug>/like/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_like(request, slug):
    post  = get_object_or_404(Post, slug=slug)
    like  = Like.objects.filter(user=request.user, post=post).first()
    liked = False

    if like:
        like.delete()
    else:
        Like.objects.create(user=request.user, post=post)
        liked = True

    return Response({'liked': liked, 'count': post.like_count()})


# ── POST /api/posts/<slug>/bookmark/
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_bookmark(request, slug):
    post       = get_object_or_404(Post, slug=slug)
    bookmark   = Bookmark.objects.filter(user=request.user, post=post).first()
    bookmarked = False

    if bookmark:
        bookmark.delete()
    else:
        Bookmark.objects.create(user=request.user, post=post)
        bookmarked = True

    return Response({'bookmarked': bookmarked})


# ── GET /api/tags/
@api_view(['GET'])
def tag_list(request):
    tags       = Tag.objects.all()
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)


# ── GET /api/categories/
@api_view(['GET'])
def category_list(request):
    categories = Category.objects.all()
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


# ── GET /api/users/<username>/
@api_view(['GET'])
def user_profile(request, username):
    user       = get_object_or_404(User, username=username)
    posts      = Post.objects.filter(author=user, status='published').order_by('-created_at')[:5]
    serializer = AuthorSerializer(user, context={'request': request})
    post_data  = PostListSerializer(posts, many=True, context={'request': request})

    return Response({
        'user':         serializer.data,
        'recent_posts': post_data.data,
    })


# ── GET /api/trending/
@api_view(['GET'])
def trending_posts(request):
    posts      = Post.objects.filter(status='published').order_by('-views')[:5]
    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)


# ── GET /api/search/?q=keyword
@api_view(['GET'])
def search_posts(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return Response({'results': [], 'query': ''})

    posts = Post.objects.filter(
        Q(title__icontains=q) |
        Q(body__icontains=q)  |
        Q(tags__name__icontains=q),
        status='published'
    ).distinct().order_by('-created_at')

    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response({'results': serializer.data, 'query': q, 'count': posts.count()})