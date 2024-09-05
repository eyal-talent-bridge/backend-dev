from django.contrib import admin
from .models import CustomUser, Job, Talent, Company, Recruiter

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'user_type', 'first_name', 'last_name', 'phone_number', 'license_type')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'license_type')
    list_filter = ('user_type', 'gender', 'is_open_to_work', 'job_type', 'license_type')
    ordering = ('-id',)

    def get_search_fields(self, request):
        if request.user.is_superuser:
            return self.search_fields
        return ('email', 'first_name', 'last_name')

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return self.list_filter
        return ('user_type', 'gender', 'is_open_to_work')

class TalentInline(admin.StackedInline):
    model = Talent
    can_delete = False
    verbose_name_plural = 'Talent Profile'

class CompanyInline(admin.StackedInline):
    model = Company
    can_delete = False
    verbose_name_plural = 'Company Profile'

class RecruiterInline(admin.StackedInline):
    model = Recruiter
    can_delete = False
    verbose_name_plural = 'Recruiter Profile'

class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'recruiter', 'job_type', 'job_sitting', 'is_relevant', 'end_date')
    search_fields = ('title', 'company__email', 'recruiter__email', 'job_type')
    list_filter = ('job_sitting', 'job_type', 'is_relevant')
    ordering = ('-id',)

    def get_list_display(self, request):
        if request.user.is_superuser:
            return self.list_display
        return ('title', 'company', 'job_type', 'end_date')

# CustomUserAdmin with inlines to handle Talent, Company, and Recruiter profiles
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'user_type', 'first_name', 'last_name', 'phone_number', 'license_type')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'license_type')
    list_filter = ('user_type',)
    inlines = []

    def get_inlines(self, request, obj=None):
        inlines = []
        if obj:
            if obj.user_type == 'Talent':
                inlines.append(TalentInline)
            elif obj.user_type == 'Company':
                inlines.append(CompanyInline)
            elif obj.user_type == 'Recruiter':
                inlines.append(RecruiterInline)
        return inlines

# Registering the models with their corresponding admin classes
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Job, JobAdmin)