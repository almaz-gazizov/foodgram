from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import CustomUser, Subscription


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'id', 'email', 'username',
        'first_name', 'last_name', 'is_staff'
    )
    list_editable = ('is_staff',)
    list_filter = ('username', 'email', 'is_staff')
    search_fields = ('username', 'email')
    empty_value_display = 'Не задано'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user', 'author')
    list_display_links = ('user',)
    list_editable = ('author',)
    empty_value_display = 'Не задано'
