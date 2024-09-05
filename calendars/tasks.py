from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_available_slots_email(recruiter_id, talent_email, available_slots):
    # Construct the email body with slot options
    email_body = "Please select a suitable meeting time from the options below:\n\n"
    for idx, slot in enumerate(available_slots):
        email_body += f"{idx + 1}. {slot[0]} to {slot[1]}\n"
        email_body += f"Reply with the number corresponding to your preferred time slot.\n\n"

    # Send the email
    send_mail(
        subject="Select a Meeting Time",
        message=email_body,
        from_email="noreply@yourdomain.com",
        recipient_list=[talent_email],
    )

@shared_task
def send_zoom_link_to_recruiter_and_talent(recruiter_email, talent_email, zoom_link):
    email_body = f"A Zoom meeting has been scheduled.\n\nJoin the meeting using this link: {zoom_link}"
    
    # Send email to Recruiter
    send_mail(
        subject="Zoom Meeting Scheduled",
        message=email_body,
        from_email="noreply@yourdomain.com",
        recipient_list=[recruiter_email],
    )
    
    # Send email to Talent
    send_mail(
        subject="Zoom Meeting Scheduled",
        message=email_body,
        from_email="noreply@yourdomain.com",
        recipient_list=[talent_email],
    )
