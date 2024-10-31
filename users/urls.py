from django.urls import path,include
from .views import *
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
    path('google-login/', google_login, name='google_login'),
    path('complete-profile/', complete_profile, name= 'complete_talent_profile'),

    


    path('auth/request-password-reset/', request_password_reset, name='request_password_reset'),
    path('auth/reset-password/<str:token>/', reset_password_confirm, name='reset_password_confirm'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    #-------------------------------------Talent--------------------------------------------------------------------------------
    path('talent/<uuid:talent_id>/open_processes/', talent_open_processes, name='talent_open_processes'),
    path('manage-cv/<uuid:talent_id>/', manage_cv, name='manage_cv'),
    path('manage-profile-pic/<uuid:user_id>/', manage_profile_pic, name='manage_profile_pic'),
    path('manage-recommendation-letter/<uuid:user_id>/', manage_recommendation_letter, name='manage_recommendation_letter'),
    path('search_talents/<uuid:job_id>/', search_talents_for_job, name='search_talents_for_job'),

    #-------------------------------------recruiter--------------------------------------------------------------------------------
    path('recruiter/<uuid:recruiter_id>/jobs/', recruiter_jobs, name='recruiter-jobs'),

    #-------------------------------------company--------------------------------------------------------------------------------
    path('company/<uuid:company_id>/recruiters/', company_recruiters, name='company_recruiters'),
    path('companies/', companies_details, name='companies_detail'),
    path('company/job/<uuid:job_id>/', manage_jobs, name='manage_jobs'),
    path('company/<uuid:company_id>/job/', create_job, name='create_job'),
    path('company/<uuid:company_id>/jobs/', company_jobs, name='company-jobs'),
    path('recruiters/<uuid:recruiter_id>/', manage_recruiters, name='company-jobs'),



# -------------------------------------general--------------------------------------------------------------------------------
    path('user/<uuid:user_id>/', user_detail, name='user_detail'),
    

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

