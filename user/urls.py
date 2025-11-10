from django.urls import path, include
from rest_framework.routers import DefaultRouter

from user.views import UserViewSet, SignInAPIView, MeAPIView, RefreshTokenAPIView

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', SignInAPIView.as_view(), name='login'),
    path('auth/refresh/', RefreshTokenAPIView.as_view(), name='token_refresh'),
    path('me/', MeAPIView.as_view(), name='me'),
]
