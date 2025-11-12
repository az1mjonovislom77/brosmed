from django.urls import path, include
from rest_framework.routers import DefaultRouter

from cashier.views import CashierViewSet

router = DefaultRouter()
router.register('cashier', CashierViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
