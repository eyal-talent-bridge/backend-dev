from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.exceptions import ValidationError
import os,re
from urllib.parse import urlparse



# Helper to validate file extensions and size
def validate_file_extension(file, allowed_extensions):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file extension. Allowed extensions are: {', '.join(allowed_extensions)}.")
        
def validate_file_size(file, max_size_mb):
    file_size = file.size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise ValidationError(f"File size exceeds the allowed limit of {max_size_mb} MB.")

# Custom Token Serializer for JWT with additional claims
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims based on the user type
        token['user_type'] = user.user_type

        if user.user_type == 'Talent':
            token['first_name'] = user.first_name
            token['last_name'] = user.last_name
        elif user.user_type == 'Company':
            token['name'] = user.name
        elif user.user_type == 'Recruiter':
            token['first_name'] = user.first_name
            token['last_name'] = user.last_name

        token['user_id'] = str(user.id)
        return token

# CustomUser Serializer
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"

# Talent Serializer (with nested CustomUser serializer)
class TalentSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    age = serializers.ReadOnlyField()  # Add the age property


    class Meta:
        model = Talent
        fields = "__all__"



    def validate_website_url(website):
        if not website:
            raise serializers.ValidationError("Website URL is required.")
        
        if not re.match(r'^https?://', website):
            raise serializers.ValidationError("Website URL must start with http:// or https://")
        
        parsed_url = urlparse(website)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise serializers.ValidationError("Invalid website URL format.")
        
        return website


    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for key, value in user_data.items():
                setattr(user, key, value)
            user.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

# Company Serializer (with nested CustomUser serializer)
class CompanySerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(required=False)

    class Meta:
        model = Company
        fields = "__all__"

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for key, value in user_data.items():
                setattr(user, key, value)
            user.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

# Recruiter Serializer (with nested CustomUser serializer)
class RecruiterSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = Recruiter
        fields = "__all__"

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user
            for key, value in user_data.items():
                setattr(user, key, value)
            user.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance



class JobSerializer(serializers.ModelSerializer):
    # Format for the 'end_date' field
    end_date = serializers.DateField(format="%d-%m-%Y", input_formats=["%d-%m-%Y", "%Y-%m-%d"])

    def update(self, instance, validated_data):
        # If 'user' field is part of the data, handle nested updates
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user  # Assuming 'user' is a ForeignKey or OneToOneField
            for key, value in user_data.items():
                setattr(user, key, value)
            user.save()

        # Update other job fields
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        return instance

    class Meta:
        model = Job
        fields = "__all__"