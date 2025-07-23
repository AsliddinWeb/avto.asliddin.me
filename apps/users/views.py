# apps/users/views.py (CLASS-BASED)
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.contrib import messages
from django.views.generic import TemplateView, UpdateView, ListView
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse


from .models import User
from apps.orders.models import Order
from apps.reviews.models import ProductWishlist, Review
from apps.products.models import UserLike


class ProfileView(LoginRequiredMixin, TemplateView):
    """Foydalanuvchi profil sahifasi"""
    template_name = 'users/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Foydalanuvchi statistikalari
        stats = {
            'total_orders': Order.objects.filter(user=user).count(),
            'pending_orders': Order.objects.filter(
                user=user,
                status__in=['pending', 'payment_pending']
            ).count(),
            'completed_orders': Order.objects.filter(
                user=user,
                status='delivered'
            ).count(),
            'total_reviews': Review.objects.filter(user=user).count(),
            'wishlist_count': ProductWishlist.objects.filter(user=user).count(),
            'liked_products': UserLike.objects.filter(user=user).count(),
        }

        # Oxirgi buyurtmalar
        recent_orders = Order.objects.filter(
            user=user
        ).select_related().order_by('-created_at')[:5]

        # Oxirgi sharhlar
        recent_reviews = Review.objects.filter(
            user=user,
            is_approved=True
        ).select_related('product').order_by('-created_at')[:5]

        context.update({
            'user': user,
            'stats': stats,
            'recent_orders': recent_orders,
            'recent_reviews': recent_reviews,
        })

        return context


class ProfileEditView(LoginRequiredMixin, View):
    """Profil tahrirlash sahifasi"""
    template_name = 'users/profile_edit.html'

    def get(self, request, *args, **kwargs):
        context = {
            'user': request.user,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user

        # Form ma'lumotlarini olish
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()

        # Validatsiya
        errors = []

        if not first_name:
            errors.append('Ism kiritish majburiy')
        elif len(first_name) < 2:
            errors.append('Ism kamida 2 ta harf kiritish kerak')

        if email and '@' not in email:
            errors.append('Email manzil noto\'g\'ri')

        # Agar xatolar bo'lsa
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Ma'lumotlarni yangilash
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save(update_fields=['first_name', 'last_name', 'email'])

            messages.success(request, 'Profil muvaffaqiyatli yangilandi!')
            return redirect('users:profile')

        context = {
            'user': user,
        }
        return render(request, self.template_name, context)


class OrderHistoryView(LoginRequiredMixin, ListView):
    """Buyurtmalar tarixi"""
    template_name = 'users/order_history.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user

        # Filter parametrlari
        status_filter = self.request.GET.get('status')

        # Base queryset
        queryset = Order.objects.filter(
            user=user
        ).select_related().order_by('-created_at')

        # Status filter
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Available statuses
        available_statuses = Order.objects.filter(
            user=user
        ).values_list('status', flat=True).distinct()

        # Status choices for display
        status_choices = dict(Order.STATUS_CHOICES)

        context.update({
            'total_orders': self.get_queryset().count(),
            'available_statuses': available_statuses,
            'status_choices': status_choices,
            'current_status': self.request.GET.get('status'),
        })

        return context


class FavoritesView(LoginRequiredMixin, ListView):
    """Sevimli mahsulotlar"""
    template_name = 'users/favorites.html'
    context_object_name = 'favorites'
    paginate_by = 24

    def get_queryset(self):
        return ProductWishlist.objects.filter(
            user=self.request.user
        ).select_related(
            'product__category', 'product__brand'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_favorites'] = self.get_queryset().count()
        return context


class UserDashboardView(LoginRequiredMixin, TemplateView):
    """Foydalanuvchi dashboard - profil bilan bir xil"""
    template_name = 'users/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Umumiy statistika
        context['stats'] = {
            'total_orders': Order.objects.filter(user=user).count(),
            'active_orders': Order.objects.filter(
                user=user,
                status__in=['pending', 'payment_pending', 'confirmed', 'preparing', 'shipped']
            ).count(),
            'completed_orders': Order.objects.filter(
                user=user,
                status='delivered'
            ).count(),
            'cancelled_orders': Order.objects.filter(
                user=user,
                status='cancelled'
            ).count(),
            'total_spent': Order.objects.filter(
                user=user,
                status='delivered'
            ).aggregate(
                total=Count('total_amount_som')
            )['total'] or 0,
            'wishlist_count': ProductWishlist.objects.filter(user=user).count(),
            'reviews_count': Review.objects.filter(user=user).count(),
        }

        # Faol buyurtmalar
        context['active_orders'] = Order.objects.filter(
            user=user,
            status__in=['pending', 'payment_pending', 'confirmed', 'preparing', 'shipped']
        ).order_by('-created_at')[:3]

        # Yaqinda ko'rilgan mahsulotlar (wishlist orqali)
        context['recent_favorites'] = ProductWishlist.objects.filter(
            user=user
        ).select_related('product').order_by('-created_at')[:6]

        return context



class UserReviewsView(LoginRequiredMixin, ListView):
    """Foydalanuvchi sharhlari"""
    model = Review
    template_name = 'users/user_reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        # Annotation bilan likes va dislikes count ni hisoblash
        return Review.objects.filter(
            user=self.request.user
        ).select_related('product__category', 'product__brand').annotate(
            likes_count=Count('votes', filter=Q(votes__vote='like')),
            dislikes_count=Count('votes', filter=Q(votes__vote='dislike'))
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Base queryset for stats
        base_qs = Review.objects.filter(user=user)

        # Sharh statistikalari
        context['review_stats'] = {
            'total_reviews': base_qs.count(),
            'approved_reviews': base_qs.filter(is_approved=True).count(),
            'pending_reviews': base_qs.filter(is_approved=False).count(),
            'featured_reviews': base_qs.filter(is_featured=True).count(),
        }

        return context


class LogoutView(LoginRequiredMixin, View):
    """Chiqish"""

    def get(self, request, *args, **kwargs):
        return render(request, 'users/logout_confirm.html')

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, 'Muvaffaqiyatli chiqib ketdingiz!')
        return redirect('/')


class UserSettingsView(LoginRequiredMixin, TemplateView):
    """Foydalanuvchi sozlamalari"""
    template_name = 'users/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        user = request.user

        # Notification settings (kelajakda)
        email_notifications = request.POST.get('email_notifications') == 'on'
        telegram_notifications = request.POST.get('telegram_notifications') == 'on'

        # Hozircha faqat message
        messages.success(request, 'Sozlamalar saqlandi!')
        return redirect('users:settings')


class DeleteAccountView(LoginRequiredMixin, View):
    """Hisobni o'chirish"""
    template_name = 'users/delete_account.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        confirmation = request.POST.get('confirmation', '').strip().lower()

        if confirmation == 'o\'chirish' or confirmation == 'ochirish':
            user = request.user
            logout(request)

            # Foydalanuvchini o'chirish o'rniga deactivate qilish
            user.is_active = False
            user.save(update_fields=['is_active'])

            messages.success(request, 'Hisobingiz muvaffaqiyatli o\'chirildi!')
            return redirect('/')
        else:
            messages.error(request, 'Tasdiqlash uchun "o\'chirish" so\'zini kiriting')
            return render(request, self.template_name)