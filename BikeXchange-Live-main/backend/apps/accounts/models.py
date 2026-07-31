"""
Custom User model for the Vutto Bike Auction Platform.

Extends Django's AbstractUser to add role-based access control
and additional profile fields.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model with role-based access control.
    
    Roles:
        BUYER - Can browse auctions and place bids
        ADMIN - Can manage auctions, view analytics, and all buyer capabilities
    """

    class Role(models.TextChoices):
        BUYER = 'BUYER', 'Buyer'
        ADMIN = 'ADMIN', 'Admin'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.BUYER,
        db_index=True,
    )
    phone = models.CharField(max_length=15, blank=True, default='')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as the primary identifier for auth
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.get_full_name()} ({self.email})'

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def display_name(self):
        full = self.get_full_name()
        return full if full.strip() else self.username
