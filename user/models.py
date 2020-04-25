import os
import time

from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class CUser(AbstractUser):
    avatar = models.ImageField(default=None)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'username': self.username,
            'avatar': self.avatar.url if self.avatar else None,
        }


class Chat(models.Model):
    from_user = models.ForeignKey(CUser, on_delete=models.CASCADE, related_name='from_user')
    to_user = models.ForeignKey(CUser, on_delete=models.CASCADE, related_name='to_user')
    last_update = models.DateTimeField(auto_now=True)

    def to_dict(self):
        return {
            'id': self.id,
            'from_user': self.from_user.to_dict(),
            'to_user': self.to_user.to_dict(),
            'updated_at': time.mktime(self.last_update.timetuple()),
        }


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    from_user = models.ForeignKey(CUser, on_delete=models.CASCADE)
    text = models.TextField()
    seen_at = models.DateTimeField(null=True, blank=True)
    file = models.FileField(null=True, blank=True)

    def to_dict(self):
        return {
            'id': self.id,
            'chat': self.chat.to_dict(),
            'from_user': self.from_user.to_dict(),
            'text': self.text,
            'file': self.file.url if self.file else None,
        }

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        self.chat.save(force_update=True)

    def delete(self, using=None, keep_parents=False):
        if self.file:
            try:
                os.remove(self.file.path)
            except:
                pass
        return super().delete(using, keep_parents)

