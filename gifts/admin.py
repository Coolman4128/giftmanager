from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Gift, Family, Notification


# Register your models here.

admin.site.register(Gift)
admin.site.register(Notification)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('family',),
        }),
    )
    list_display = UserAdmin.list_display + ('family',)

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    pass

