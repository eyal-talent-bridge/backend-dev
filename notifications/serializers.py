# serializers.py
from rest_framework import serializers
from .models import CompanyNotification

class CompanyNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyNotification
        fields = "__all__"