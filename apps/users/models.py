from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class UserManager(BaseUserManager):
    """Custom user manager"""

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number is required')

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    """Custom User model"""
    username = None  # Username o'rniga phone ishlatamiz

    # Phone number (login uchun)
    phone = PhoneNumberField(
        unique=True,
        verbose_name="Telefon raqami"
    )

    # Telegram ma'lumotlar
    telegram_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        verbose_name="Telegram Chat ID"
    )
    telegram_username = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Telegram Username"
    )

    # Qo'shimcha ma'lumotlar
    is_phone_verified = models.BooleanField(
        default=False,
        verbose_name="Telefon tasdiqlangan"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()  # QO'SHING!

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def __str__(self):
        if self.first_name:
            return f"{self.first_name} ({self.phone})"
        return str(self.phone)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
