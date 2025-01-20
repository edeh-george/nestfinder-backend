from django.contrib import admin
from django.urls import path, re_path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static


version = "api/v1/"
urlpatterns = [
     # YOUR PATTERNS
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    #Custom apps and admin site
    path("admin/", admin.site.urls),
    path(f"{version}", include('userauth.urls')),
    path(f"{version}", include('apartment.urls')),
    path(f"{version}", include('review.urls')),
    path(f"{version}", include('payment.urls')),
    # path('', include('social_auth.urls')),
    #social auth
    path('', include('social_django.urls', namespace='social')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
