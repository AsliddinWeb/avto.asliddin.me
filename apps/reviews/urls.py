# apps/reviews/urls.py
from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    # Mahsulot sharhlari
    path('product/<slug:product_slug>/', views.ReviewListView.as_view(), name='product_reviews'),

    # Sharh yozish
    path('create/<slug:product_slug>/', views.ReviewCreateView.as_view(), name='review_create'),

    # Sharhni tahrirlash va o'chirish
    path('<int:pk>/edit/', views.ReviewUpdateView.as_view(), name='review_edit'),
    path('<int:pk>/delete/', views.ReviewDeleteView.as_view(), name='review_delete'),

    # Maxsus sahifalar
    path('featured/', views.FeaturedReviewsView.as_view(), name='featured_reviews'),
    path('recent/', views.RecentReviewsView.as_view(), name='recent_reviews'),

    # API endpoints (AJAX)
    path('api/product/<slug:product_slug>/reviews/', views.ProductReviewsAPIView.as_view(), name='product_reviews_api'),
    path('api/<int:review_id>/like/', views.ReviewLikeToggleView.as_view(), name='review_like_toggle'),
    path('api/<int:review_id>/report/', views.ReviewReportView.as_view(), name='review_report'),
    path('api/wishlist/<int:product_id>/toggle/', views.WishlistToggleView.as_view(), name='wishlist_toggle'),
]