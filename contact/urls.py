from django.urls import path

from contact.views import ContactView, HealthView, MetricsView

urlpatterns = [
    path('contact', ContactView.as_view(), name='contact'),
    path('health', HealthView.as_view(), name='health'),
    path('metrics', MetricsView.as_view(), name='metrics'),
]
