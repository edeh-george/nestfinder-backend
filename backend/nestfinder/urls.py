from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

version = "api/v1/"
urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("admin/", admin.site.urls),
    path(f"{version}", include("userauth.urls")),
    path(f"{version}", include("apartment.urls")),
    path(f"{version}", include("review.urls")),
    path(f"{version}", include("payment.urls")),
    path("api/oauth/", include("social_django.urls", namespace="social")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
