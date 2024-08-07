'''
admin.py
'''


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, Guardian

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('signup_id', 'password')}),
        ('Personal info', {'fields': ()}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('signup_id', 'password1', 'password2'),
        }),
    )
    list_display = ('signup_id', 'is_staff', 'is_superuser')
    search_fields = ('signup_id',)
    ordering = ('signup_id',)

admin.site.register(User, UserAdmin)
admin.site.register(Profile)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ('guardian_id', 'name', 'phone_number', 'relationship', 'user')
    search_fields = ('name', 'user__signup_id')
    list_filter = ('relationship',)

admin.site.register(Guardian, GuardianAdmin)