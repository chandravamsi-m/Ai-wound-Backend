from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'role', 'status', 'isActive')
    list_filter = ('role', 'status', 'isActive')
    search_fields = ('name', 'email')
