from django.contrib import admin

from contact.models import ContactRequest, RequestLog


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'ai_category', 'ai_sentiment', 'ai_used', 'created_at')
    list_filter = ('ai_category', 'ai_sentiment', 'ai_used', 'created_at')
    search_fields = ('name', 'email', 'comment')
    readonly_fields = ('id', 'created_at', 'client_ip')


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ('method', 'path', 'status_code', 'duration_ms', 'created_at')
    list_filter = ('method', 'status_code', 'created_at')
    readonly_fields = ('created_at',)
