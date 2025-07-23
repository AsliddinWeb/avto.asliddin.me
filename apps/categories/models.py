from django.db import models
from django.urls import reverse
from django.utils.text import slugify

class Category(models.Model):
    """Mahsulot kategoriyalari"""
    name = models.CharField(max_length=100, verbose_name="Nomi")
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name="Asosiy kategoriya"
    )
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name="Rasm"
    )
    description = models.TextField(blank=True, verbose_name="Tavsif")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    order = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse('categories:category_detail', kwargs={'slug': self.slug})

    @property
    def is_parent(self):
        return self.parent is None

    def get_children(self):
        return self.subcategories.filter(is_active=True)