from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.core.exceptions import ValidationError
import os, re
from urllib.parse import urlparse


# Helper to validate phone number
def validate_phone_number(phone_number):
    if not phone_number.isdigit() or len(phone_number) < 9 or len(phone_number) > 15:
        raise serializers.ValidationError("Enter a valid phone number 9 to 15 digits.")
    return phone_number


# Custom Token Serializer for JWT with additional claims
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['user_type'] = user.user_type

        # Add additional claims based on user type
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


# CustomUser Serializer with phone number validation
class CustomUserSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(validators=[validate_phone_number])

    class Meta:
        model = CustomUser
        fields = "__all__"



# class CompleteProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['phone_number',]




class CompleteProfileSerializer(serializers.ModelSerializer):
    gender = serializers.CharField(source='talent_profile.gender', read_only=False)
    birth_date = serializers.DateField(source='talent_profile.birth_date', read_only=False)
    age = serializers.SerializerMethodField()
    phone_number = serializers.CharField()

    class Meta:
        model = CustomUser
        fields = ['phone_number', 'gender', 'birth_date', 'age']

    def get_age(self, obj):
        if hasattr(obj, 'talent_profile') and obj.talent_profile.birth_date:
            age = obj.talent_profile.age
            print(f"Calculated age: {age}")  # Add this for debugging
            return age
        print("Age not found")  # Add this for debugging
        return None

    def update(self, instance, validated_data):
        # Update fields from CustomUser
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()

        # Update fields from Talent
        talent_data = validated_data.get('talent_profile', {})
        talent_profile = instance.talent_profile
        if talent_profile:
            talent_profile.gender = talent_data.get('gender', talent_profile.gender)
            talent_profile.birth_date = talent_data.get('birth_date', talent_profile.birth_date)
            talent_profile.save()

        return instance

class TalentSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()  # This now includes `phone_number`
    age = serializers.ReadOnlyField()

    class Meta:
        model = Talent
        fields = "__all__"

    def validate_email(self, email):
        public_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = email.split('@')[1]
        if domain not in public_domains:
            raise serializers.ValidationError('Invalid email domain')
        return email

    def validate_website_url(self, website):
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


# Company Serializer
class CompanySerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(required=False)

    class Meta:
        model = Company
        fields = "__all__"

    def validate_email(self, email):
        public_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
        domain = email.split('@')[1]
        if domain in public_domains:
            raise serializers.ValidationError('Invalid email domain')
        return email

    def validate_website_url(self, url):
        if not url:
            raise serializers.ValidationError("Website URL is required.")
        if not re.match(r'^https?://', url):
            raise serializers.ValidationError("Website URL must start with http:// or https://")
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise serializers.ValidationError("Invalid website URL format.")
        return url

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


# Recruiter Serializer
class RecruiterSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = Recruiter
        fields = "__all__"

    def validate_email(self, email):
        # Assuming `self.context` provides `company_id` for additional validation
        company_id = self.context.get('company_id')
        company = Company.objects.filter(id=company_id).first()

        if not company:
            raise serializers.ValidationError('Company not found')

        company_domain = company.email.split('@')[1] if company.email else None
        recruiter_domain = email.split('@')[1]
        
        if not company_domain or company_domain != recruiter_domain:
            raise serializers.ValidationError('Email domain does not match company domain')
        return email

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


# Job Serializer
class JobSerializer(serializers.ModelSerializer):
    end_date = serializers.DateField(format="%d-%m-%Y", input_formats=["%d-%m-%Y", "%Y-%m-%d"])

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user = instance.user  # Assuming 'user' is a ForeignKey or OneToOneField
            for key, value in user_data.items():
                setattr(user, key, value)
            user.save()

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        return instance

    class Meta:
        model = Job
        fields = "__all__"