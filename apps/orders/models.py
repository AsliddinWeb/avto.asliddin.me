from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class Order(models.Model):
    """Buyurtmalar"""

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('payment_pending', 'To\'lov kutilmoqda'),
        ('confirmed', 'Tasdiqlandi'),
        ('preparing', 'Tayyorlanmoqda'),
        ('shipped', 'Jo\'natildi'),
        ('delivered', 'Yetkazildi'),
        ('cancelled', 'Bekor qilindi'),
        ('payment_rejected', 'To\'lov rad etildi'),
    ]

    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )

    # Order details
    order_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Buyurtma raqami"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Holati"
    )

    # Pricing
    total_amount_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Umumiy summa (USD)"
    )
    total_amount_som = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Umumiy summa (UZS)"
    )
    usd_rate_used = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Ishlatilgan dollar kursi"
    )

    # Payment
    payment_screenshot = models.ImageField(
        upload_to='payments/',
        null=True,
        blank=True,
        verbose_name="To'lov cheki"
    )
    payment_card_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="To'lov qilingan karta"
    )

    # Delivery info
    delivery_address = models.TextField(
        null=True,
        blank=True,
        verbose_name="Yetkazish manzili"
    )
    delivery_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Yetkazish telefoni"
    )

    # Oferta agreement
    oferta_agreed = models.BooleanField(
        default=False,
        verbose_name="Oferta bilan tanishdi"
    )
    oferta_agreed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Oferta vaqti"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Admin notes
    admin_notes = models.TextField(
        blank=True,
        verbose_name="Admin izohlar"
    )

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Order number generation
        if not self.order_number:
            self.order_number = self.generate_order_number()

        # Auto-calculate SOM amount
        if self.total_amount_usd and self.usd_rate_used:
            self.total_amount_som = self.total_amount_usd * self.usd_rate_used

        # Oferta agreement timestamp
        if self.oferta_agreed and not self.oferta_agreed_at:
            self.oferta_agreed_at = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.order_number} - {self.user.phone}"

    def generate_order_number(self):
        """Buyurtma raqami yaratish"""
        import random
        import string
        while True:
            number = ''.join(random.choices(string.digits, k=8))
            number = f"AK{number}"
            if not Order.objects.filter(order_number=number).exists():
                return number

    @property
    def formatted_total_som(self):
        return f"{self.total_amount_som:,.0f} so'm"

    @property
    def is_paid(self):
        return self.payment_screenshot is not None

    @property
    def can_cancel(self):
        return self.status in ['pending', 'payment_pending']


class OrderItem(models.Model):
    """Buyurtma mahsulotlari"""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Buyurtma"
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name="Mahsulot"
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Miqdori"
    )
    price_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,  # QO'SHING
        blank=True,  # QO'SHING
        verbose_name="Narxi (USD)"
    )
    price_som = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,  # QO'SHING
        blank=True,  # QO'SHING
        verbose_name="Narxi (UZS)"
    )

    # Product snapshot (agar product o'chirilsa)
    product_name = models.CharField(
        max_length=200,
        blank=True,  # QO'SHING
        verbose_name="Mahsulot nomi"
    )
    product_image = models.ImageField(
        upload_to='order_products/',
        null=True,
        blank=True,
        verbose_name="Mahsulot rasmi"
    )

    class Meta:
        verbose_name = "Buyurtma mahsuloti"
        verbose_name_plural = "Buyurtma mahsulotlari"

    def save(self, *args, **kwargs):
        # Save product snapshot
        if self.product:
            self.product_name = self.product.name
            self.price_usd = self.product.price_usd
            self.price_som = self.product.price_som
            if self.product.main_image:
                self.product_image = self.product.main_image
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def total_usd(self):
        if self.price_usd:  # None check qo'shildi
            return self.price_usd * self.quantity
        return 0

    @property
    def total_som(self):
        if self.price_som:  # None check qo'shildi
            return self.price_som * self.quantity
        return 0


class OrderStatusHistory(models.Model):
    """Buyurtma holati tarixi"""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name="Buyurtma"
    )
    status = models.CharField(
        max_length=20,
        choices=Order.STATUS_CHOICES,
        verbose_name="Holat"
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Izoh"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kim o'zgartirdi"
    )

    class Meta:
        verbose_name = "Holat tarixi"
        verbose_name_plural = "Holat tarixi"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()}"