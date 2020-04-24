from django.contrib import admin

from user.models import CUser, Message, Chat

admin.site.register(CUser)
admin.site.register(Message)
admin.site.register(Chat)
