from django.urls import path,include
from .views import *
from .auth_views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    #-------------------------------------auth--------------------------------------------------------------------------------
    path('auth/signin/', signin, name='signin'),
    path('auth/signup/talent/', talent_signup, name='talent_signup'),
    path('auth/signup/recruiter/', recruiter_signup, name='recruiter_signup'),
    path('auth/signup/company/', company_signup, name='company_signup'),
    path('auth/logout',logout, name='logout'),
    


    path('social-auth/', include('social_django.urls', namespace='social')),
    path('auth/request-password-reset/', request_password_reset, name='request_password_reset'),
    path('auth/reset-password/<str:token>/', reset_password_confirm, name='reset_password_confirm'),
    path('auth/facebook/', talent_facebook_login, name='talent_facebook_login'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    #-------------------------------------Talent--------------------------------------------------------------------------------
    path('talent/<uuid:talent_id>/open_processes/', talent_open_processes, name='talent_open_processes'),
    path('manage-cv/', manage_cv, name='manage_cv'),
    path('manage_recommendation_letter/', manage_recommendation_letter, name='manage_letter'),
    #-------------------------------------recruiter--------------------------------------------------------------------------------
    path('recruiter/check_requirements/', check_requirements, name='check_requirements'),


    #-------------------------------------company--------------------------------------------------------------------------------
    path('company/<uuid:company_id>/recruiters/', company_recruiters, name='company_recruiters'),
    path('companies/', companies_details, name='companies_detail'),
    path('company/job/<uuid:job_id>/', manage_jobs, name='manage_jobs'),
    path('company/<uuid:company_id>/job/', create_job, name='create_job'),
     path('company/<uuid:company_id>/jobs/', company_jobs, name='company-jobs'),



# -------------------------------------general--------------------------------------------------------------------------------
    path('user/<uuid:user_id>/', user_detail, name='user_detail'),
    


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

