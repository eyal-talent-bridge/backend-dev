from django.urls import path
from .views import *

urlpatterns = [
    path('support/',contact_us, name = 'mail_support'),

]