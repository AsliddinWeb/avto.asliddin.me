from django.db import models
from django.urls import reverse
from django.utils.text import slugify

class Brand(models.Model):
    """Avtomobil brendlari"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nomi")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    logo = models.ImageField(
        upload_to='brands/',
        blank=True,
        null=True,
        verbose_name="Logo"
    )
    description = models.TextField(blank=True, verbose_name="Tavsif")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Brend"
        verbose_name_plural = "Brendlar"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('brands:brand_detail', kwargs={'slug': self.slug})  # ✅

class CarModel(models.Model):
    """Avtomobil modellari"""
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='car_models',
        verbose_name="Brend"
    )
    name = models.CharField(max_length=100, verbose_name="Model nomi")
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    year_from = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Yildan"
    )
    year_to = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Yilgacha"
    )
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avtomobil modeli"
        verbose_name_plural = "Avtomobil modellari"
        unique_together = ['brand', 'name']
        ordering = ['brand__name', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.brand.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        years = ""
        if self.year_from or self.year_to:
            years = f" ({self.year_from or ''}-{self.year_to or ''})"
        return f"{self.brand.name} {self.name}{years}"

    def get_absolute_url(self):
        return reverse('brands:car_model_detail', kwargs={
            'brand_slug': self.brand.slug,
            'model_slug': self.slug
        })  # ✅