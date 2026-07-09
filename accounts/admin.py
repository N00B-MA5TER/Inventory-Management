from django.contrib import admin

from accounts.models import ActionLog, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at')
    list_filter = ('user',)
    ordering = ('-created_at',)
    readonly_fields = ('user', 'action', 'created_at')
