from rest_framework import serializers
from .models import User, Post, Tag, Category, Comment


class AuthorSerializer(serializers.ModelSerializer):
    follower_count  = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ['id', 'username', 'bio', 'avatar', 'follower_count', 'following_count']

    def get_follower_count(self, obj):
        return obj.follower_count()

    def get_following_count(self, obj):
        return obj.following_count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tag
        fields = ['id', 'name', 'slug']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug']


class CommentSerializer(serializers.ModelSerializer):
    author  = AuthorSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model  = Comment
        fields = ['id', 'author', 'body', 'created_at', 'replies']

    def get_replies(self, obj):
        return CommentSerializer(obj.replies.all(), many=True).data


class PostListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for post lists — no full body"""
    author      = AuthorSerializer(read_only=True)
    tags        = TagSerializer(many=True, read_only=True)
    category    = CategorySerializer(read_only=True)
    like_count  = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model  = Post
        fields = [
            'id', 'title', 'slug', 'excerpt', 'cover_image',
            'author', 'category', 'tags',
            'status', 'views', 'read_time',
            'like_count', 'comment_count',
            'created_at', 'updated_at',
        ]

    def get_like_count(self, obj):
        return obj.like_count()

    def get_comment_count(self, obj):
        return obj.comment_count()


class PostDetailSerializer(PostListSerializer):
    """Full serializer for single post — includes body and comments"""
    comments = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['body', 'comments']

    def get_comments(self, obj):
        top_level = obj.comments.filter(parent=None)
        return CommentSerializer(top_level, many=True).data


class PostCreateSerializer(serializers.ModelSerializer):
    """For creating/updating posts"""
    class Meta:
        model  = Post
        fields = ['title', 'body', 'cover_image', 'category', 'tags', 'status']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        post.tags.set(tags)
        return post

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance