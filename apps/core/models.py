from django.db import models

class Settings(models.Model):
    """Sayt umumiy sozlamalari"""
    usd_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Dollar kursi",
        help_text="1 USD = ? UZS"
    )
    payment_card_number = models.CharField(
        max_length=20,
        verbose_name="To'lov karta raqami"
    )
    site_name = models.CharField(
        max_length=100,
        default="Avtokontinent.uz",
        verbose_name="Sayt nomi"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sozlama"
        verbose_name_plural = "Sozlamalar"

    def __str__(self):
        return f"Dollar kursi: {self.usd_rate}"

class Banner(models.Model):
    """Main page bannerlar"""
    title = models.CharField(max_length=200, verbose_name="Sarlavha")
    slug = models.SlugField(max_length=200, unique=True, blank=True)  # QO'SHING
    description = models.TextField(blank=True, verbose_name="Tavsif")
    image = models.ImageField(upload_to='banners/', verbose_name="Rasm")
    link_url = models.URLField(blank=True, verbose_name="Havola")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Bannerlar"
        ordering = ['order']

    def save(self, *args, **kwargs):  # QO'SHING
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title