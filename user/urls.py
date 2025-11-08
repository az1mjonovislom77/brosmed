from django.urls import path, include
from rest_framework.routers import DefaultRouter

from user.views import UserViewSet, SignInAPIView

router = DefaultRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', SignInAPIView.as_view(), name='login'),
]
