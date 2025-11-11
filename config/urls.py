from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('department/', include('department.urls')),
    path('utils/', include('utils.urls')),
    path('doctor/', include('doctor.urls')),
    path('reception/', include('reception.urls')),
    path('laboratory/', include('laboratory.urls')),

    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
