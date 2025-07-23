# apps/users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Profil
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),

    # Dashboard
    path('dashboard/', views.UserDashboardView.as_view(), name='dashboard'),

    # Buyurtmalar tarixi
    path('orders/', views.OrderHistoryView.as_view(), name='order_history'),

    # Sevimlilar
    path('favorites/', views.FavoritesView.as_view(), name='favorites'),

    # Sharhlar
    path('reviews/', views.UserReviewsView.as_view(), name='user_reviews'),

    # Sozlamalar
    path('settings/', views.UserSettingsView.as_view(), name='settings'),

    # Hisobni o'chirish
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),

    # Chiqish
    path('logout/', views.LogoutView.as_view(), name='logout'),
]