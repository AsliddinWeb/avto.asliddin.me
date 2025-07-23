from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Review(models.Model):
    """Mahsulot sharhlari"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Mahsulot"
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Baho (1-5)"
    )
    comment = models.TextField(
        max_length=1000,
        verbose_name="Sharh"
    )

    # Moderation
    is_approved = models.BooleanField(
        default=True,
        verbose_name="Tasdiqlangan"
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name="Tanlangan sharh"
    )

    # Admin response
    admin_response = models.TextField(
        blank=True,
        verbose_name="Admin javobi"
    )
    admin_response_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Admin javob vaqti"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"
        ordering = ['-created_at']
        unique_together = ['user', 'product']  # Har user faqat 1 ta sharh

    def __str__(self):
        return f"{self.user.phone} - {self.product.name} ({self.rating}⭐)"

    @property
    def star_display(self):
        return "⭐" * self.rating + "☆" * (5 - self.rating)

    # @property
    # def likes_count(self):
    #     return self.votes.filter(vote='like').count()
    #
    # @property
    # def dislikes_count(self):
    #     return self.votes.filter(vote='dislike').count()


class ReviewLike(models.Model):
    """Sharh like/dislike"""

    VOTE_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name="Sharh"
    )
    vote = models.CharField(
        max_length=10,
        choices=VOTE_CHOICES,
        verbose_name="Ovoz"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sharh ovozi"
        verbose_name_plural = "Sharh ovozlari"
        unique_together = ['user', 'review']

    def __str__(self):
        return f"{self.user.phone} - {self.vote}"


class ProductWishlist(models.Model):
    """Foydalanuvchi sevimli mahsulotlari"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Foydalanuvchi"
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
        verbose_name="Mahsulot"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sevimli mahsulot"
        verbose_name_plural = "Sevimli mahsulotlar"
        unique_together = ['user', 'product']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.phone} - {self.product.name}"