from django.urls import path
from .views import *

urlpatterns = [
    path('support/',contact_us, name = 'mail_support'),
    path('company/<uuid:company_id>/', manage_company_notifications, name='manage_company_notifications'),


]