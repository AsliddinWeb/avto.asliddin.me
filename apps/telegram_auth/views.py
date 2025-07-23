# apps/telegram_auth/views.py (CLASS-BASED VERSIYA)
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import json
import logging

from .models import UserCode
from apps.users.models import User

logger = logging.getLogger(__name__)


class LoginPageView(TemplateView):
    """Login sahifasi - class-based"""
    template_name = 'telegram_auth/login.html'

    def dispatch(self, request, *args, **kwargs):
        # Agar user allaqachon login qilgan bo'lsa
        if request.user.is_authenticated:
            return redirect('/')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bot_username'] = 'asliddin767bot'  # .env dan olish mumkin
        context['step'] = 'show_instructions'
        return context


@method_decorator(csrf_exempt, name='dispatch')
class VerifyCodeView(View):
    """5 xonali kodni tekshirish - AJAX class-based"""

    def post(self, request, *args, **kwargs):
        try:
            # JSON ma'lumotlarni olish
            data = json.loads(request.body)
            code_5digit = data.get('code', '').strip()

            # Kod formatini tekshirish
            if not code_5digit:
                return JsonResponse({
                    'success': False,
                    'error': '5 xonali kodni kiriting'
                })

            if len(code_5digit) != 5 or not code_5digit.isdigit():
                return JsonResponse({
                    'success': False,
                    'error': '5 xonali raqam kiriting'
                })

            # Kodni bazadan qidirish
            user_code = UserCode.objects.filter(
                code=code_5digit,
                is_used=False
            ).first()

            if not user_code:
                return JsonResponse({
                    'success': False,
                    'error': 'Kod noto\'g\'ri yoki ishlatilgan'
                })

            # Kod muddatini tekshirish (2 daqiqa)
            if user_code.is_expired:
                # Eski kodni o'chirish
                user_code.delete()
                return JsonResponse({
                    'success': False,
                    'error': 'Kod muddati tugagan. Botdan yangi kod oling.'
                })

            # User yaratish yoki topish
            phone = user_code.phone
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    'first_name': 'Telegram User',
                    'telegram_chat_id': user_code.telegram_chat_id,
                    'telegram_username': user_code.telegram_username,
                    'is_phone_verified': True
                }
            )

            # Agar user allaqachon mavjud bo'lsa, telegram ma'lumotlarini yangilash
            if not created:
                user.telegram_chat_id = user_code.telegram_chat_id
                user.telegram_username = user_code.telegram_username or user.telegram_username
                user.is_phone_verified = True
                user.save(update_fields=['telegram_chat_id', 'telegram_username', 'is_phone_verified'])

            # Kodni ishlatilgan deb belgilash
            user_code.is_used = True
            user_code.save(update_fields=['is_used'])

            # Django session'ga login qilish
            login(request, user)

            logger.info(f"User {user.phone} successfully logged in via Telegram")

            return JsonResponse({
                'success': True,
                'message': f'Xush kelibsiz, {user.first_name}!',
                'redirect_url': '/'  # Bosh sahifaga yo'naltirish
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Noto\'g\'ri ma\'lumot formati'
            })
        except Exception as e:
            logger.error(f"Verify code error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Serverda xatolik yuz berdi'
            })

    def get(self, request, *args, **kwargs):
        return JsonResponse({
            'success': False,
            'error': 'Faqat POST so\'rov qabul qilinadi'
        })


class LoginSuccessView(TemplateView):
    """Login muvaffaqiyatli sahifasi"""
    template_name = 'telegram_auth/login_success.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('telegram_auth:login_page')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context


class CheckCodeStatusView(View):
    """Kod holati tekshirish - opsional AJAX"""

    def get(self, request, *args, **kwargs):
        code = request.GET.get('code', '').strip()

        if not code or len(code) != 5:
            return JsonResponse({
                'valid': False,
                'message': '5 xonali kod kiriting'
            })

        # Kod mavjudligini tekshirish
        user_code = UserCode.objects.filter(
            code=code,
            is_used=False
        ).first()

        if not user_code:
            return JsonResponse({
                'valid': False,
                'message': 'Kod topilmadi'
            })

        if user_code.is_expired:
            return JsonResponse({
                'valid': False,
                'message': 'Kod muddati tugagan'
            })

        return JsonResponse({
            'valid': True,
            'message': 'Kod to\'g\'ri',
            'phone': str(user_code.phone)
        })


class BotInstructionsView(TemplateView):
    """Bot bilan ishlash yo'riqnomasi"""
    template_name = 'telegram_auth/bot_instructions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bot_username'] = 'asliddin767bot'
        context['bot_link'] = 'https://t.me/asliddin767bot'
        return context