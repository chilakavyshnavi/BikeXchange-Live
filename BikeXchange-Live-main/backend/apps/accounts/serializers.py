"""
Serializers for user registration, authentication, and profile management.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration with password validation."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone',
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username=value.lower()).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile display and updates."""

    display_name = serializers.ReadOnlyField()
    total_bids = serializers.SerializerMethodField()
    auctions_won = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'role', 'display_name', 'total_bids',
            'auctions_won', 'created_at',
        ]
        read_only_fields = ['id', 'email', 'role', 'created_at']

    def get_total_bids(self, obj):
        return obj.bids.count()

    def get_auctions_won(self, obj):
        return obj.won_auctions.count()


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for embedding in other responses."""

    display_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name']
