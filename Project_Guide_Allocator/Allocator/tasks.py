# tasks.py in your Django app
from celery import shared_task
from .email_sender import send_mail_page, send_mail_with_attachment

@shared_task
def send_email_task(to_email, subject, message):
    try:
        send_mail_page(to_email, subject, message)
        return {'result': 'Email sent successfully'}
    except Exception as e:
        return {'error': str(e)}
    
@shared_task
def send_email_report(address, subject, message, pdf):
    try:
        send_mail_with_attachment(address, subject, message, pdf)
        return {'result': 'Email sent successfully'}
    except Exception as e:
        return {'error': str(e)}

# @shared_task
# def generate_pdf_task(data):
#     pdf = generate_pdf(data)  # A function that generates a PDF
#     # Save or send the generated PDF