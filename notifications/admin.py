from django.contrib import admin
from .models import TalentNotificationLog,CompanyNotification
from users.models import Talent, Job  # Assuming these are defined in the `users` app

# Register Talent for autocomplete if not already registered
if not admin.site.is_registered(Talent):
    @admin.register(Talent)
    class TalentAdmin(admin.ModelAdmin):
        search_fields = ('name',)  # Enable searching by Talent name

# No need to register Job again if it's already registered
# Assuming it has the required search_fields in the 'users' app

# Register TalentNotificationLog with autocomplete fields
@admin.register(TalentNotificationLog)
class TalentNotificationLogAdmin(admin.ModelAdmin):
    list_display = ('talent', 'job', 'notified_at')  # Display these fields in the admin list view
    search_fields = ('talent__name', 'job__title')   # Enable searching by talent name and job title
    list_filter = ('notified_at',)                   # Enable filtering by notification date
    ordering = ('-notified_at',)                     # Orders by the most recent notifications
    autocomplete_fields = ('talent', 'job')          # Autocomplete fields for talent and job



class CompanyNotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'subject', 'created_at', 'end_date', 'is_read')
    list_filter = ('is_read', 'created_at', 'end_date')
    search_fields = ('recipient__user__username', 'subject', 'message')
    ordering = ('-created_at',)

    # This makes the 'is_read' field editable from the list display
    list_editable = ('is_read',)

    # Customize how the admin form displays
    fieldsets = (
        (None, {
            'fields': ('recipient', 'subject', 'message', 'end_date', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    # Read-only fields (created_at should be auto-populated and not editable)
    readonly_fields = ('created_at',)

admin.site.register(CompanyNotification, CompanyNotificationAdmin)