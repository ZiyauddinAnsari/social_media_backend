from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Profile, Post, Comment, Media, Like, Tag
from .validators import validate_media_file

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    display_name = serializers.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'display_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        display_name = validated_data.pop('display_name', '')
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # Create profile
        Profile.objects.create(
            user=user,
            display_name=display_name or user.email.split('@')[0]
        )
        
        return user


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'date_joined', 'profile')
        read_only_fields = ('id', 'date_joined')

    def get_profile(self, obj) -> dict | None:
        try:
            profile = obj.profile
            return {
                'display_name': profile.display_name,
                'bio': profile.bio,
                'avatar': profile.avatar.url if profile.avatar else None,
            }
        except Profile.DoesNotExist:
            return None


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('display_name', 'bio', 'avatar')


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = ('id', 'file', 'content_type', 'size', 'width', 'height')
        read_only_fields = ('id','content_type','size','width','height')

    def create(self, validated_data):
        file = validated_data['file']
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            meta = validate_media_file(file)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'file': list(e.messages)})
        validated_data.update(meta)
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id','name')


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField(read_only=True)
    replies_count = serializers.IntegerField(source='replies.count', read_only=True)

    class Meta:
        model = Comment
        fields = ('id','post','author','text','parent','created_at','replies_count')
        read_only_fields = ('id','author','created_at','replies_count','post')

    def get_author(self, obj):
        return {'id': obj.author_id, 'email': obj.author.email}


class PostSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField(read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = ('id','author','title','content','privacy','tags','created_at','updated_at','media','likes_count','comments_count')
        read_only_fields = ('id','author','created_at','updated_at','media','likes_count','comments_count')

    def get_author(self, obj):
        return {'id': obj.author_id, 'email': obj.author.email}

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        user = self.context['request'].user
        post = Post.objects.create(author=user, **validated_data)
        for tag_obj in tags_data:
            tag, _ = Tag.objects.get_or_create(name=tag_obj['name'])
            post.tags.add(tag)
        return post

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags_data is not None:
            instance.tags.clear()
            for tag_obj in tags_data:
                tag, _ = Tag.objects.get_or_create(name=tag_obj['name'])
                instance.tags.add(tag)
        return instance


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('id','post','user','created_at')
        read_only_fields = ('id','user','created_at','post')