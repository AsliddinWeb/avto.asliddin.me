# apps/orders/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, TemplateView
from django.views import View
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Q
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.utils import timezone
from decimal import Decimal

from .models import Order, OrderItem, OrderStatusHistory
from apps.products.models import Product
from apps.core.models import Settings


class CheckoutView(LoginRequiredMixin, TemplateView):
    """Rasmiylashtirish sahifasi"""
    template_name = 'orders/checkout.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Cart ma'lumotlari (session dan yoki frontend dan keladi)
        # Hozircha demo uchun
        context['cart_items'] = []  # Frontend dan keladi
        context['cart_total_usd'] = Decimal('0.00')
        context['cart_total_som'] = Decimal('0.00')

        # Dollar kursi
        try:
            settings = Settings.objects.first()
            context['usd_rate'] = settings.usd_rate if settings else Decimal('12500')
            context['payment_card'] = settings.payment_card_number if settings else ''
        except:
            context['usd_rate'] = Decimal('12500')
            context['payment_card'] = ''

        return context


    def post(self, request, *args, **kwargs):
        """Buyurtma yaratish"""
        try:
            # Form ma'lumotlari
            delivery_address = request.POST.get('delivery_address', '').strip()
            delivery_phone = request.POST.get('delivery_phone', '').strip()
            notes = request.POST.get('notes', '').strip()
            cart_items_json = request.POST.get('cart_items', '')

            # Validatsiya
            if not delivery_address:
                messages.error(request, 'Yetkazish manzilini kiriting')
                return redirect('orders:checkout')

            if not delivery_phone:
                messages.error(request, 'Yetkazish telefon raqamini kiriting')
                return redirect('orders:checkout')

            if not cart_items_json:
                messages.error(request, 'Savatcha bo\'sh')
                return redirect('cart:cart')

            # Cart ma'lumotlarini parse qilish
            import json
            try:
                cart_items = json.loads(cart_items_json)
            except json.JSONDecodeError:
                messages.error(request, 'Savatcha ma\'lumotlari noto\'g\'ri')
                return redirect('cart:cart')

            if not cart_items:
                messages.error(request, 'Savatcha bo\'sh')
                return redirect('cart:cart')

            # Dollar kursi
            settings = Settings.objects.first()
            usd_rate = settings.usd_rate if settings else Decimal('12500')

            # Jami summani hisoblash va validatsiya
            total_usd = Decimal('0')
            valid_items = []

            for item in cart_items:
                try:
                    product_id = int(item.get('product_id', 0))
                    quantity = int(item.get('quantity', 1))
                    price_usd = Decimal(str(item.get('price_usd', 0)))

                    # Mahsulot mavjudligini tekshirish
                    product = Product.objects.get(id=product_id, is_active=True)

                    if quantity <= 0:
                        continue

                    # Real price bilan tekshirish (security)
                    if abs(price_usd - product.price_usd) > Decimal('0.01'):
                        messages.error(request, f'Mahsulot "{product.name}" narxi o\'zgargan. Sahifani yangilang.')
                        return redirect('cart:cart')

                    item_total = price_usd * quantity
                    total_usd += item_total

                    valid_items.append({
                        'product': product,
                        'quantity': quantity,
                        'price_usd': price_usd,
                        'price_som': price_usd * usd_rate,
                        'total_usd': item_total,
                        'total_som': item_total * usd_rate
                    })

                except (ValueError, Product.DoesNotExist):
                    continue

            if not valid_items:
                messages.error(request, 'Savatda haqiqiy mahsulot yo\'q')
                return redirect('cart:cart')

            # Yetkazish narxi (ixtiyoriy)
            delivery_fee_usd = Decimal('0')  # Hozircha bepul
            if total_usd < 50:  # $50 dan kam bo'lsa $5 yetkazish
                delivery_fee_usd = Decimal('5')

            final_total_usd = total_usd + delivery_fee_usd
            final_total_som = final_total_usd * usd_rate

            # Buyurtma yaratish
            order = Order.objects.create(
                user=request.user,
                total_amount_usd=final_total_usd,
                total_amount_som=final_total_som,
                usd_rate_used=usd_rate,
                delivery_address=delivery_address,
                delivery_phone=delivery_phone,
                status='pending'
            )

            # OrderItem'larni yaratish
            for item in valid_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price_usd=item['price_usd'],
                    price_som=item['price_som'],
                    product_name=item['product'].name,
                    product_image=item['product'].main_image
                )

            # Status history
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                comment='Buyurtma yaratildi' + (f'. Izoh: {notes}' if notes else ''),
                created_by=request.user
            )

            messages.success(request, f'Buyurtma #{order.order_number} muvaffaqiyatli yaratildi!')
            return redirect('orders:order_confirm', order_id=order.id)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Checkout error: {str(e)}')

            messages.error(request, 'Buyurtma yaratishda xatolik yuz berdi. Qayta urinib ko\'ring.')
            return redirect('orders:checkout')


class OrderConfirmView(LoginRequiredMixin, DetailView):
    """Buyurtmani tasdiqlash sahifasi"""
    model = Order
    template_name = 'orders/order_confirm.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        # Order items
        context['order_items'] = order.items.all().select_related('product')

        # Oferta kelishuvi holati
        context['oferta_required'] = not order.oferta_agreed

        # To'lov ma'lumotlari
        try:
            settings = Settings.objects.first()
            context['payment_card'] = settings.payment_card_number if settings else ''
        except:
            context['payment_card'] = ''

        return context

    def post(self, request, *args, **kwargs):
        """Oferta bilan tanishish"""
        order = self.get_object()

        oferta_agreed = request.POST.get('oferta_agreed') == 'on'

        if oferta_agreed:
            order.oferta_agreed = True
            order.oferta_agreed_at = timezone.now()
            order.save(update_fields=['oferta_agreed', 'oferta_agreed_at'])

            messages.success(request, 'Oferta bilan tanishdingiz. Endi to\'lov qilishingiz mumkin!')
        else:
            messages.error(request, 'Oferta bilan tanishish majburiy!')

        return redirect('orders:order_confirm', order_id=order.id)


class PaymentView(LoginRequiredMixin, DetailView):
    """To'lov sahifasi"""
    model = Order
    template_name = 'orders/payment.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user,
            oferta_agreed=True  # Faqat oferta kelishilgan buyurtmalar
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        # To'lov ma'lumotlari
        try:
            settings = Settings.objects.first()
            context['payment_card'] = settings.payment_card_number if settings else ''
        except:
            context['payment_card'] = ''

        # To'lov mumkinmi
        context['can_pay'] = order.status in ['pending', 'payment_pending']

        return context

    def post(self, request, *args, **kwargs):
        """To'lov cheki yuklash"""
        order = self.get_object()

        payment_screenshot = request.FILES.get('payment_screenshot')
        payment_card_number = request.POST.get('payment_card_number', '').strip()

        if not payment_screenshot:
            messages.error(request, 'To\'lov chekini yuklash majburiy!')
            return redirect('orders:payment', order_id=order.id)

        # To'lov ma'lumotlarini saqlash
        order.payment_screenshot = payment_screenshot
        order.payment_card_number = payment_card_number
        order.status = 'payment_pending'
        order.save(update_fields=['payment_screenshot', 'payment_card_number', 'status'])

        # Status history
        OrderStatusHistory.objects.create(
            order=order,
            status='payment_pending',
            comment='To\'lov cheki yuklandi',
            created_by=request.user
        )

        messages.success(request, 'To\'lov cheki yuklandi! Tez orada tekshirib ko\'ramiz.')
        return redirect('orders:order_success', order_id=order.id)


class OrderSuccessView(LoginRequiredMixin, DetailView):
    """Buyurtma muvaffaqiyatli sahifasi"""
    model = Order
    template_name = 'orders/order_success.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        context['order_items'] = order.items.all().select_related('product')

        # Keyingi qadam haqida ma'lumot
        if order.status == 'payment_pending':
            context['next_step'] = 'To\'lov tekshirilmoqda'
        elif order.status == 'confirmed':
            context['next_step'] = 'Buyurtma tayyorlanmoqda'
        else:
            context['next_step'] = 'Buyurtma jarayonda'

        return context


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Buyurtma detali sahifasi"""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        # Order items
        context['order_items'] = order.items.all().select_related('product')

        # Status history
        context['status_history'] = order.status_history.all().order_by('-created_at')

        # Status display
        context['status_display'] = order.get_status_display()

        # Buyurtmani bekor qilish mumkinmi
        context['can_cancel'] = order.can_cancel

        return context


class OrderListView(LoginRequiredMixin, ListView):
    """Foydalanuvchi buyurtmalari"""
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user

        # Filter parametrlari
        status_filter = self.request.GET.get('status')

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

        # Status choices
        status_choices = dict(Order.STATUS_CHOICES)

        # Statistika
        context.update({
            'available_statuses': available_statuses,
            'status_choices': status_choices,
            'current_status': self.request.GET.get('status'),
            'total_orders': Order.objects.filter(user=user).count(),
            'pending_orders': Order.objects.filter(
                user=user,
                status__in=['pending', 'payment_pending']
            ).count(),
            'completed_orders': Order.objects.filter(
                user=user,
                status='delivered'
            ).count(),
        })

        return context


class OrderStatusView(LoginRequiredMixin, DetailView):
    """Buyurtma statusi tekshirish"""
    model = Order
    template_name = 'orders/order_status.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        # Status timeline
        status_timeline = [
            {'status': 'pending', 'name': 'Kutilmoqda', 'completed': False},
            {'status': 'payment_pending', 'name': 'To\'lov kutilmoqda', 'completed': False},
            {'status': 'confirmed', 'name': 'Tasdiqlandi', 'completed': False},
            {'status': 'preparing', 'name': 'Tayyorlanmoqda', 'completed': False},
            {'status': 'shipped', 'name': 'Jo\'natildi', 'completed': False},
            {'status': 'delivered', 'name': 'Yetkazildi', 'completed': False},
        ]

        # Current status index
        status_order = ['pending', 'payment_pending', 'confirmed', 'preparing', 'shipped', 'delivered']
        try:
            current_index = status_order.index(order.status)
            for i, step in enumerate(status_timeline):
                if i <= current_index:
                    step['completed'] = True
        except ValueError:
            pass

        context['status_timeline'] = status_timeline
        context['status_history'] = order.status_history.all().order_by('-created_at')

        return context


@method_decorator(require_POST, name='dispatch')
class OrderCancelView(LoginRequiredMixin, View):
    """Buyurtmani bekor qilish"""

    def post(self, request, *args, **kwargs):
        try:
            order = get_object_or_404(
                Order,
                order_number=kwargs['order_number'],
                user=request.user
            )

            if not order.can_cancel:
                return JsonResponse({
                    'success': False,
                    'error': 'Bu buyurtmani bekor qilib bo\'lmaydi'
                })

            # Buyurtmani bekor qilish
            order.status = 'cancelled'
            order.save(update_fields=['status'])

            # Status history
            OrderStatusHistory.objects.create(
                order=order,
                status='cancelled',
                comment='Foydalanuvchi tomonidan bekor qilindi',
                created_by=request.user
            )

            return JsonResponse({
                'success': True,
                'message': 'Buyurtma muvaffaqiyatli bekor qilindi'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class OrderTrackingView(TemplateView):
    """Buyurtmani kuzatish (order number orqali)"""
    template_name = 'orders/order_tracking.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        order_number = self.request.GET.get('order_number', '').strip()
        phone = self.request.GET.get('phone', '').strip()

        if order_number and phone:
            try:
                order = Order.objects.get(
                    order_number=order_number,
                    user__phone=phone
                )
                context['order'] = order
                context['order_items'] = order.items.all().select_related('product')
                context['status_history'] = order.status_history.all().order_by('-created_at')
            except Order.DoesNotExist:
                context['error'] = 'Buyurtma topilmadi yoki telefon raqam mos kelmadi'

        return context


class OrderInvoiceView(LoginRequiredMixin, DetailView):
    """Buyurtma invoice/chek"""
    model = Order
    template_name = 'orders/order_invoice.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object

        context['order_items'] = order.items.all().select_related('product')

        # Sayt ma'lumotlari
        try:
            settings = Settings.objects.first()
            context['site_name'] = settings.site_name if settings else 'Avtokontinent.uz'
        except:
            context['site_name'] = 'Avtokontinent.uz'

        return context