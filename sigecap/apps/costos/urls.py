from django.urls import path
from . import views

app_name = 'costos'

urlpatterns = [
    path('', views.dashboard_costos, name='dashboard'),
]
