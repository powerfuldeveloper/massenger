import os
import time

from django.contrib.auth.models import AbstractUser
from django.db import models
# Create your models here.
from jdatetime import GregorianToJalali


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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def to_dict(self):
        updated = self.created_at != self.updated_at
        created_at = GregorianToJalali(self.created_at.year, self.created_at.month, self.created_at.day) \
            .getJalaliList()
        created_at = list(created_at)
        created_at.extend([self.created_at.hour,  self.created_at.minute, self.created_at.second, ])
        updated_at = GregorianToJalali(self.updated_at.year, self.updated_at.month, self.updated_at.day) \
            .getJalaliList()
        updated_at = list(updated_at)
        updated_at.extend([self.updated_at.hour,  self.updated_at.minute, self.updated_at.second,])
        return {
            'id': self.id,
            'chat': self.chat.to_dict(),
            'from_user': self.from_user.to_dict(),
            'text': self.text,
            'updated': updated,
            'file': self.file.url if self.file else None,
            'seen': self.seen_at is not None,
            'created_at': created_at,
            'updated_at': updated_at,
        }

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        self.chat.save(force_update=True)

    def delete(self, using=None, keep_parents=False):
        if Message.objects.filter(file=self.file).count() == 1:
            if self.file:
                try:
                    os.remove(self.file.path)
                except:
                    pass
        return super().delete(using, keep_parents)
