from django.contrib import admin

from accounts.models import ActionLog, Profile, RoleUpgradeRequest


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'full_name', 'phone')
    list_filter = ('role',)


@admin.register(RoleUpgradeRequest)
class RoleUpgradeRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'submitted_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status',)


@admin.register(ActionLog)
class ActionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at')
    list_filter = ('user',)
    ordering = ('-created_at',)
    readonly_fields = ('user', 'action', 'created_at')
