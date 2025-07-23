# apps/reviews/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Avg, Q
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy

from .models import Review, ReviewLike, ProductWishlist
from apps.products.models import Product


class ReviewListView(ListView):
    """Mahsulot sharhlari ro'yxati"""
    model = Review
    template_name = 'reviews/review_list.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        self.product = get_object_or_404(
            Product,
            slug=self.kwargs['product_slug'],
            is_active=True
        )

        return Review.objects.filter(
            product=self.product,
            is_approved=True
        ).select_related('user').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product

        # Sharh statistikalari
        reviews_stats = self.get_queryset().aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id'),
            rating_5=Count('id', filter=Q(rating=5)),
            rating_4=Count('id', filter=Q(rating=4)),
            rating_3=Count('id', filter=Q(rating=3)),
            rating_2=Count('id', filter=Q(rating=2)),
            rating_1=Count('id', filter=Q(rating=1)),
        )

        context['review_stats'] = reviews_stats

        # Foydalanuvchi bu mahsulotga sharh yozganmi
        if self.request.user.is_authenticated:
            context['user_review'] = Review.objects.filter(
                user=self.request.user,
                product=self.product
            ).first()

        return context


class ReviewCreateView(LoginRequiredMixin, CreateView):
    """Sharh yozish"""
    model = Review
    template_name = 'reviews/review_create.html'
    fields = ['rating', 'comment']

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            Product,
            slug=kwargs['product_slug'],
            is_active=True
        )

        # Foydalanuvchi allaqachon sharh yozganmi
        if Review.objects.filter(
                user=request.user,
                product=self.product
        ).exists():
            messages.error(request, 'Siz bu mahsulotga allaqachon sharh yozgansiz!')
            return redirect('products:product_detail', slug=self.product.slug)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.product = self.product
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'Sharhingiz muvaffaqiyatli qo\'shildi!')
        return self.product.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    """Sharhni tahrirlash"""
    model = Review
    template_name = 'reviews/review_edit.html'
    fields = ['rating', 'comment']

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Sharh muvaffaqiyatli yangilandi!')
        return self.object.product.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.product
        return context


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    """Sharhni o'chirish"""
    model = Review
    template_name = 'reviews/review_delete.html'

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def get_success_url(self):
        messages.success(self.request, 'Sharh muvaffaqiyatli o\'chirildi!')
        return self.object.product.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.object.product
        return context


@method_decorator(require_POST, name='dispatch')
class ReviewLikeToggleView(LoginRequiredMixin, View):
    """Sharhga like/dislike - AJAX"""

    def post(self, request, *args, **kwargs):
        try:
            review = get_object_or_404(Review, id=kwargs['review_id'])
            vote_type = request.POST.get('vote')  # 'like' yoki 'dislike'

            if vote_type not in ['like', 'dislike']:
                return JsonResponse({
                    'success': False,
                    'error': 'Noto\'g\'ri ovoz turi'
                })

            # Oldingi ovozni tekshirish
            existing_vote = ReviewLike.objects.filter(
                user=request.user,
                review=review
            ).first()

            if existing_vote:
                if existing_vote.vote == vote_type:
                    # Bir xil ovoz - olib tashlash
                    existing_vote.delete()
                    voted = False
                else:
                    # Boshqa ovoz - o'zgartirish
                    existing_vote.vote = vote_type
                    existing_vote.save(update_fields=['vote'])
                    voted = True
            else:
                # Yangi ovoz
                ReviewLike.objects.create(
                    user=request.user,
                    review=review,
                    vote=vote_type
                )
                voted = True

            # Statistikani hisoblash
            likes_count = ReviewLike.objects.filter(
                review=review,
                vote='like'
            ).count()

            dislikes_count = ReviewLike.objects.filter(
                review=review,
                vote='dislike'
            ).count()

            return JsonResponse({
                'success': True,
                'voted': voted,
                'vote_type': vote_type,
                'likes_count': likes_count,
                'dislikes_count': dislikes_count
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


@method_decorator(require_POST, name='dispatch')
class WishlistToggleView(LoginRequiredMixin, View):
    """Wishlist qo'shish/olib tashlash - AJAX"""

    def post(self, request, *args, **kwargs):
        try:
            product = get_object_or_404(
                Product,
                id=kwargs['product_id'],
                is_active=True
            )

            wishlist_item, created = ProductWishlist.objects.get_or_create(
                user=request.user,
                product=product
            )

            if not created:
                # Agar mavjud bo'lsa, olib tashlash
                wishlist_item.delete()
                added = False
                message = 'Mahsulot sevimlilardan olib tashlandi'
            else:
                added = True
                message = 'Mahsulot sevimlilarga qo\'shildi'

            # Wishlist count
            wishlist_count = ProductWishlist.objects.filter(
                user=request.user
            ).count()

            return JsonResponse({
                'success': True,
                'added': added,
                'message': message,
                'wishlist_count': wishlist_count
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class ProductReviewsAPIView(View):
    """Mahsulot sharhlari API - AJAX pagination uchun"""

    def get(self, request, *args, **kwargs):
        try:
            product = get_object_or_404(
                Product,
                slug=kwargs['product_slug'],
                is_active=True
            )

            page = int(request.GET.get('page', 1))
            rating_filter = request.GET.get('rating')

            # Base queryset
            reviews_qs = Review.objects.filter(
                product=product,
                is_approved=True
            ).select_related('user')

            # Rating filter
            if rating_filter and rating_filter.isdigit():
                reviews_qs = reviews_qs.filter(rating=int(rating_filter))

            reviews_qs = reviews_qs.order_by('-created_at')

            # Pagination
            paginator = Paginator(reviews_qs, 10)
            reviews_page = paginator.get_page(page)

            # Serialize data
            reviews_data = []
            for review in reviews_page:
                # User likes/dislikes
                user_vote = None
                if request.user.is_authenticated:
                    vote_obj = ReviewLike.objects.filter(
                        user=request.user,
                        review=review
                    ).first()
                    if vote_obj:
                        user_vote = vote_obj.vote

                # Vote counts
                likes_count = ReviewLike.objects.filter(
                    review=review,
                    vote='like'
                ).count()

                dislikes_count = ReviewLike.objects.filter(
                    review=review,
                    vote='dislike'
                ).count()

                reviews_data.append({
                    'id': review.id,
                    'user_name': review.user.first_name or 'Foydalanuvchi',
                    'rating': review.rating,
                    'comment': review.comment,
                    'created_at': review.created_at.strftime('%d.%m.%Y'),
                    'likes_count': likes_count,
                    'dislikes_count': dislikes_count,
                    'user_vote': user_vote,
                    'is_featured': review.is_featured,
                    'admin_response': review.admin_response,
                })

            return JsonResponse({
                'success': True,
                'reviews': reviews_data,
                'has_next': reviews_page.has_next(),
                'has_previous': reviews_page.has_previous(),
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_reviews': paginator.count,
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class FeaturedReviewsView(ListView):
    """Tanlangan sharhlar"""
    model = Review
    template_name = 'reviews/featured_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        return Review.objects.filter(
            is_approved=True,
            is_featured=True
        ).select_related('user', 'product').order_by('-created_at')


class RecentReviewsView(ListView):
    """Oxirgi sharhlar"""
    model = Review
    template_name = 'reviews/recent_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        return Review.objects.filter(
            is_approved=True
        ).select_related('user', 'product').order_by('-created_at')


class ReviewReportView(LoginRequiredMixin, View):
    """Sharhdan shikoyat qilish - AJAX"""

    def post(self, request, *args, **kwargs):
        try:
            review = get_object_or_404(Review, id=kwargs['review_id'])
            reason = request.POST.get('reason', '').strip()

            if not reason:
                return JsonResponse({
                    'success': False,
                    'error': 'Shikoyat sababini kiriting'
                })

            # Shikoyat logic (kelajakda ReportModel yaratish mumkin)
            # Hozircha faqat success message

            return JsonResponse({
                'success': True,
                'message': 'Shikoyatingiz yuborildi. Tekshirib ko\'ramiz.'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })