# Generated by Django 5.0.8 on 2024-09-05 07:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='user_type',
            field=models.CharField(blank=True, choices=[('Talent', 'Talent'), ('Company', 'Company'), ('Recruiter', 'Recruiter')], max_length=50, null=True),
        ),
        migrations.AlterModelTable(
            name='customuser',
            table='custom_users',
        ),
    ]
