from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from contact.frontend_views import LandingView

urlpatterns = [
    path('', LandingView.as_view(), name='landing'),
    path('admin/', admin.site.urls),
    path('api/', include('contact.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
