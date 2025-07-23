# apps/telegram_auth/urls.py
from django.urls import path
from .views import (
    LoginPageView,
    VerifyCodeView,
    LoginSuccessView,
    CheckCodeStatusView,
    BotInstructionsView
)

app_name = 'telegram_auth'

urlpatterns = [
    path('login/', LoginPageView.as_view(), name='login_page'),
    path('verify-code/', VerifyCodeView.as_view(), name='verify_code'),
    path('success/', LoginSuccessView.as_view(), name='login_success'),
    path('check-code-status/', CheckCodeStatusView.as_view(), name='check_code_status'),
    path('instructions/', BotInstructionsView.as_view(), name='bot_instructions'),
]
