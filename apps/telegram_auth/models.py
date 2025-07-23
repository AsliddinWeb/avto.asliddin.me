# apps/telegram_auth/models.py

from django.db import models
from django.utils import timezone
from datetime import timedelta
from phonenumber_field.modelfields import PhoneNumberField
import random
import string


# TempCode modeli OLIB TASHLANADI - kerak emas


class UserCode(models.Model):
    """5 xonali kod (bot dan keladigan)"""
    phone = PhoneNumberField(verbose_name="Telefon")
    code = models.CharField(max_length=5)  # 4 dan 5 ga o'zgaradi
    telegram_chat_id = models.BigIntegerField()
    telegram_username = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Foydalanuvchi kodi"
        verbose_name_plural = "Foydalanuvchi kodlari"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.phone} - {self.code}"

    @staticmethod
    def generate_code():
        """5 xonali kod yaratish"""
        return ''.join(random.choices(string.digits, k=5))

    @property
    def is_expired(self):
        """2 daqiqa ichida"""
        return timezone.now() > (self.created_at + timedelta(minutes=2))

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired