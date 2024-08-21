from django.urls import path
from .views import chart_view

app_name = "logger"

urlpatterns = [
    path("", chart_view, name='chart_view'),
]

