from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class Product(models.Model):
    """Mahsulotlar"""
    name = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(verbose_name="Tavsif")

    # Narx (dollar da)
    price_usd = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Narxi (USD)"
    )

    # Foreign Keys
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.CASCADE,
        verbose_name="Kategoriya"
    )
    brand = models.ForeignKey(
        'brands.Brand',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Brend"
    )
    car_models = models.ManyToManyField(
        'brands.CarModel',
        blank=True,
        verbose_name="Avtomobil modellari"
    )

    # Rasmlar
    main_image = models.ImageField(
        upload_to='products/',
        verbose_name="Asosiy rasm"
    )

    # Video
    video_url = models.URLField(
        blank=True,
        null=True,
        help_text="YouTube video linki",
        verbose_name="Video URL"
    )

    # Statistika
    views_count = models.PositiveIntegerField(default=0, verbose_name="Ko'rishlar")
    likes_count = models.PositiveIntegerField(default=0, verbose_name="Likelar")

    # Status
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    is_featured = models.BooleanField(default=False, verbose_name="Tavsiya qilingan")
    in_stock = models.BooleanField(default=True, verbose_name="Omborda bor")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})  # ✅

    @property
    def price_som(self):
        """Narxni som da qaytarish"""
        from apps.core.models import Settings
        try:
            settings = Settings.objects.first()
            if settings:
                return self.price_usd * settings.usd_rate
        except:
            pass
        return self.price_usd * 12500  # Default kurs

    @property
    def formatted_price_som(self):
        """Formatlangan narx"""
        return f"{self.price_som:,.0f} so'm"

    @property
    def embed_video_url(self):
        """YouTube URL'ni embed formatiga o'zgartirish"""
        if self.video_url:
            if 'watch?v=' in self.video_url:
                return self.video_url.replace('watch?v=', 'embed/')
            elif 'youtu.be/' in self.video_url:
                video_id = self.video_url.split('/')[-1]
                return f'https://www.youtube.com/embed/{video_id}'
        return self.video_url


class ProductImage(models.Model):
    """Mahsulot qo'shimcha rasmlari"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Mahsulot"
    )
    image = models.ImageField(upload_to='products/', verbose_name="Rasm")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")

    class Meta:
        verbose_name = "Mahsulot rasmi"
        verbose_name_plural = "Mahsulot rasmlari"
        ordering = ['order']

    def __str__(self):
        return f"{self.product.name} - Rasm {self.order}"

class UserLike(models.Model):
    """Foydalanuvchi like qilgan mahsulotlar"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Mahsulot"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Like"
        verbose_name_plural = "Likelar"
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user} - {self.product.name}"