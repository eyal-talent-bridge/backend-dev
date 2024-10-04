from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

# Custom upload paths for various file types
def cv_upload_path(instance, filename):
    return f'assets/users/{instance.user_id}/cvs/{filename}'

def profile_picture_upload_path(instance, filename):
    return f'assets/users/{instance.user_id}/profile_pictures/{filename}'

def recommendation_letter_upload_path(instance, filename):
    return f'assets/users/{instance.user_id}/recommendation_letters/{filename}'

# Main user model extending AbstractUser
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('Talent', 'Talent'),
        ('Company', 'Company'),
        ('Recruiter', 'Recruiter'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES,null=True, blank=True,default='Talent')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    accept_terms = models.BooleanField(default=True)
    license_type = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'
        db_table = 'custom_users'

   

    def __str__(self):
        return self.email


# Talent model extending CustomUser for specific fields
class Talent(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='talent_profile')
    gender = models.CharField(max_length=255, blank=True, null=True)
    is_open_to_work = models.BooleanField(default=False,blank=True, null=True)
    residence = models.CharField(max_length=255, blank=True, null=True)
    about_me = models.TextField(blank=True, null=True)
    job_type = models.CharField(max_length=255, blank=True, null=True)
    job_sitting = models.CharField(max_length=255, blank=True, null=True)
    field_of_interest = models.JSONField(default=dict, blank=True)
    social_links = models.JSONField(default=list, blank=True)
    companies_black_list = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True, null=True)
    languages = models.JSONField(default=list, blank=True, null=True)
    certificates = models.TextField(max_length=250, blank=True, null=True)
    open_processes = models.JSONField(blank=True, null=True)
    cv = models.FileField(upload_to=cv_upload_path, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=profile_picture_upload_path, blank=True, null=True)
    recommendation_letter = models.FileField(upload_to=recommendation_letter_upload_path, blank=True, null=True)

    def __str__(self):
        return self.user.email
    
    db_table = 'Talents'

# Company model extending CustomUser for specific fields
class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # UUID primary key
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='company_profile')
    name = models.CharField(max_length=200, blank=True, null=True)
    website = models.URLField(max_length=200, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    job_history = models.JSONField(default=dict, blank=True, null=True)
    divisions = models.JSONField(default=list, blank=True)
    open_jobs = models.ManyToManyField('Job', related_name='companies', blank=True)

    db_table = 'Companies'

    def __str__(self):
        return self.name or self.user.email

# Recruiter model extending CustomUser for specific fields
class Recruiter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='recruiter_profile')
    gender = models.CharField(max_length=255, blank=True, null=True)
    division = models.CharField(max_length=255, blank=True, null=True)
    position = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='company_recruiters', null=True, blank=True)
    my_searchings = models.JSONField(default=dict, blank=True, null=True)
    working_time = models.JSONField(default=dict, blank=True, null=True)
    profile_picture = models.ImageField(upload_to=recommendation_letter_upload_path, blank=True, null=True)

    db_table = 'Recruiters'

# Job model with proper ForeignKey references
class Job(models.Model):
    JOB_SITTING = (
        ("Office", "Office"),
        ("Remote", "Remote"),
        ("Hybrid", "Hybrid"),
        ("Other", "Other"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs', null=True)  # Job belongs to a company
    recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE, related_name='jobs')  
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=200,blank=True, null=True)
    requirements = models.JSONField(default=list, blank=True)
    salary = models.FloatField(blank=True, null=True)
    job_type = models.CharField(max_length=200)
    job_sitting = models.CharField(max_length=255, choices=JOB_SITTING)
    division = models.CharField(max_length=200,blank=True, null=True)
    end_date = models.DateField(blank=True, null=True) 
    is_relevant = models.BooleanField(default=False,blank=True, null=True)
    relevant_talents = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    db_table = 'Jobs'

    def __str__(self):
        return self.title