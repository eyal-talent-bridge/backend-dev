from django.contrib import admin
from .models import *

class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id','recruiter', 'talent', 'created_at','updated_at')
    search_fields = ('recruiter', 'talent', 'created_at')
    list_filter = ('id','recruiter', 'talent', 'created_at','updated_at')
    ordering = ('-created_at',)


class MessageAdmin(admin.ModelAdmin):
    list_display = ('id','conversation', 'sender', 'content', 'created_at')
    search_fields = ('conversation', 'sender', 'content', 'created_at')
    list_filter = ('id','conversation', 'sender', 'content', 'created_at')
    ordering = ('-created_at',)


admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)  # Register your models here.
                    

