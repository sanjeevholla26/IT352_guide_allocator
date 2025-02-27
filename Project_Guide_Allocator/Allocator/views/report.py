from django.http import HttpResponseRedirect
from django.urls import reverse
from ..decorators import authorize_resource
from ..models import ChoiceList, Role
from django.contrib import messages
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
from ..tasks import send_email_report

logo_path = 'Allocator/static/nitkLogo.png'

@authorize_resource
def generate_student_pdf(request, id):
    # Fetch all students from the database
    allocations = ChoiceList.objects.all()

    for allocation in allocations:
        if allocation.event.id != id:
            continue

        # Create a PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        # Get the default stylesheet and customize heading
        styles = getSampleStyleSheet()

        # Create the heading paragraph
        main_heading_style = styles['Heading1']
        main_heading_style.alignment = 1  # Center alignment
        main_heading_style.fontSize = 28  # Larger font size for the main heading
        main_heading_style.textColor = colors.black  # Black color for the main heading

        # Create the secondary heading style
        sub_heading_style = styles['Heading1']
        sub_heading_style.alignment = 1  # Center alignment
        sub_heading_style.fontSize = 22  # Slightly smaller font size for the subheading
        sub_heading_style.textColor = colors.black  # Black color for the subheading

        # Create the main and sub-headings
        main_heading = Paragraph("National Institute of Technology Surathkal", main_heading_style)
        sub_heading = Paragraph("PROJECT ALLOCATION DETAILS", sub_heading_style)

        data = [
            ['Field', 'Details'],  # Table header
            ['Name', allocation.student.user.first_name+' '+allocation.student.user.last_name],  # Student's name
            ['Professor', allocation.current_allocation.user.first_name+' '+allocation.current_allocation.user.last_name],  # Professor name
            ['Email', allocation.student.user.email],  # Email address
            ['Date of Allocation', datetime.now().strftime("%Y-%m-%d")]  # Allocation date
        ]

        # Create the table with two columns (Field and Details)
        table = Table(data, colWidths=[2*inch, 4*inch])
        
        # Define table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey), 
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), 
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
            ('FONTSIZE', (0, 0), (-1, 0), 12),  
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12), 
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),  
            ('GRID', (0, 0), (-1, -1), 1, colors.black)  
        ])
        table.setStyle(style)

        logo = Image(logo_path, width=1.6 * inch, height=1.2 * inch)
        
        # Build the PDF with the heading and the table
        elements = []
        elements.append(logo)  # Add the logo to the top left
        elements.append(Spacer(1, 0.1 * inch))  # Add some space after the logo
        elements.append(main_heading)  # Add the main heading
        elements.append(Spacer(1, 0.2 * inch))  # Add some space after the main heading
        elements.append(sub_heading)  # Add the sub-heading
        elements.append(Spacer(1, 0.5 * inch))  # Add space between heading and table
        elements.append(table)

        def add_page_border(canvas, doc):
            # Get the page width and height
            width, height = A4

            # Set the stroke color and line width
            canvas.setStrokeColorRGB(0, 0, 0)  # Black color for the border
            canvas.setLineWidth(2)  # Thickness of the border

            # Draw the rectangle (border) around the entire page
            canvas.rect(20, 20, width - 40, height - 40)

        # Add the page border to the PDF
        doc.build(elements, onFirstPage=add_page_border, onLaterPages=add_page_border)

        # Get the PDF content from the buffer
        pdf = buffer.getvalue()
        buffer.close()

        # Create the email for the specific student

        subject='Your Project Allotment Details'
        body=f"Dear {data[1][1]},\n\nPlease find attached your project allotment details."
        to=[data[3][1]] 

        # send_email_report(to, subject, body, pdf)
        send_email_report.delay(to, subject, body, pdf)

    messages.success(request, "Allocation reports have been sent successfully to all students."),
    return HttpResponseRedirect(reverse('create_cluster', args=(id,)))

@authorize_resource
def generate_faculty_pdf(request, id):
    # Fetch all students from the database
    allocations = ChoiceList.objects.all()
    prof_student_map = {}

    for allocation in allocations:
        if allocation.event.id != id:
            continue

        if allocation.current_allocation.user not in prof_student_map:
            prof_student_map[allocation.current_allocation.user] = []

        prof_student_map[allocation.current_allocation.user].append(allocation.student)

    for prof in prof_student_map.keys():
        # Create a PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        # Get the default stylesheet and customize heading
        styles = getSampleStyleSheet()
        
        # Create the heading paragraph
        main_heading_style = styles['Heading1']
        main_heading_style.alignment = 1  # Center alignment
        main_heading_style.fontSize = 28  # Larger font size for the main heading
        main_heading_style.textColor = colors.black  # Black color for the main heading

        # Create the secondary heading style
        sub_heading_style = styles['Heading1']
        sub_heading_style.alignment = 1  # Center alignment
        sub_heading_style.fontSize = 22  # Slightly smaller font size for the subheading
        sub_heading_style.textColor = colors.black  # Black color for the subheading

        # Create the main and sub-headings
        main_heading = Paragraph("National Institute of Technology Surathkal", main_heading_style)
        sub_heading = Paragraph("PROJECT ALLOCATION DETAILS", sub_heading_style)

        data = [
            ['Student Name', 'Branch', 'CGPA', 'Email'],  # Table header
        ]
        for student in prof_student_map[prof]:
            data.append([student.user.get_full_name(), student.branch, student.cgpa, student.user.edu_email])

        # Create the table with two columns (Field and Details)
        table = Table(data, colWidths=[1.5*inch]*4)
        
        # Define table style
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey), 
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), 
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
            ('FONTSIZE', (0, 0), (-1, 0), 12),  
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12), 
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),  
            ('GRID', (0, 0), (-1, -1), 1, colors.black)  
        ])
        table.setStyle(style)

        logo = Image(logo_path, width=1.6 * inch, height=1.2 * inch)
        
        # Build the PDF with the heading and the table
        elements = []
        elements.append(logo)  # Add the logo to the top left
        elements.append(Spacer(1, 0.1 * inch))  # Add some space after the logo
        elements.append(main_heading)  # Add the main heading
        elements.append(Spacer(1, 0.2 * inch))  # Add some space after the main heading
        elements.append(sub_heading)  # Add the sub-heading
        elements.append(Spacer(1, 0.5 * inch))  # Add space between heading and table
        elements.append(table)

        def add_page_border(canvas, doc):
            # Get the page width and height
            width, height = A4

            # Set the stroke color and line width
            canvas.setStrokeColorRGB(0, 0, 0)  # Black color for the border
            canvas.setLineWidth(2)  # Thickness of the border

            # Draw the rectangle (border) around the entire page
            canvas.rect(20, 20, width - 40, height - 40)

        # Add the page border to the PDF
        doc.build(elements, onFirstPage=add_page_border, onLaterPages=add_page_border)

        # Get the PDF content from the buffer
        pdf = buffer.getvalue()
        buffer.close()

        # Create the email for the specific student

        subject='Major Project Allotment Details'
        body="Respected Sir/Madam,\n\nPlease find attached the project allotment details."
        to=[prof.edu_email]

        # send_email_report(to, subject, body, pdf)
        send_email_report.delay(to, subject, body, pdf)

    messages.success(request, "Allocation reports have been sent successfully to all faculty."),
    return HttpResponseRedirect(reverse('create_cluster', args=(id,)))

@authorize_resource
def generate_admin_pdf(request, id):
    allocations = ChoiceList.objects.all()

    # Prepare the PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)


    styles = getSampleStyleSheet()
    
    # Create the heading paragraph
    main_heading_style = styles['Heading1']
    main_heading_style.alignment = 1  # Center alignment
    main_heading_style.fontSize = 28  # Larger font size for the main heading
    main_heading_style.textColor = colors.black  # Black color for the main heading

    # Create the secondary heading style
    sub_heading_style = styles['Heading1']
    sub_heading_style.alignment = 1  # Center alignment
    sub_heading_style.fontSize = 22  # Slightly smaller font size for the subheading
    sub_heading_style.textColor = colors.black  # Black color for the subheading

    # Create the main and sub-headings
    main_heading = Paragraph("National Institute of Technology Surathkal", main_heading_style)
    sub_heading = Paragraph("PROJECT ALLOCATION DETAILS", sub_heading_style)

    # Prepare the data table for the PDF
    data = [
        ['Student Username', 'Student Email', 'Allocated Faculty'],  
    ]

    for allocation in allocations:
        if allocation.event.id != id:
            continue
        student_name = allocation.student.user.get_full_name()
        student_email = allocation.student.user.edu_email  
        allocated_faculty = allocation.current_allocation.user.username 
        data.append([student_name, student_email, allocated_faculty])

    table = Table(data, colWidths=[2 * inch, 3 * inch, 2 * inch])
    
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  
        ('FONTSIZE', (0, 0), (-1, 0), 12), 
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12), 
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),  
        ('GRID', (0, 0), (-1, -1), 1, colors.black)  
    ])
    table.setStyle(style)

    logo = Image(logo_path, width=1.6 * inch, height=1.2 * inch)
        
    # Build the PDF with the heading and the table
    elements = []
    elements.append(logo)  # Add the logo to the top left
    elements.append(Spacer(1, 0.1 * inch))  # Add some space after the logo
    elements.append(main_heading)  # Add the main heading
    elements.append(Spacer(1, 0.2 * inch))  # Add some space after the main heading
    elements.append(sub_heading)  # Add the sub-heading
    elements.append(Spacer(1, 0.5 * inch))  # Add space between heading and table
    elements.append(table)

    def add_page_border(canvas, doc):
        # Get the page width and height
        width, height = A4

        # Set the stroke color and line width
        canvas.setStrokeColorRGB(0, 0, 0)  # Black color for the border
        canvas.setLineWidth(2)  # Thickness of the border

        # Draw the rectangle (border) around the entire page
        canvas.rect(20, 20, width - 40, height - 40)

    # Add the page border to the PDF
    doc.build(elements, onFirstPage=add_page_border, onLaterPages=add_page_border)

    # Get the PDF content from the buffer
    pdf = buffer.getvalue()
    buffer.close()

    # Fetch all admin users
    admin_role = Role.objects.get(role_name="admin")  
    admin_emails = admin_role.users.values_list('edu_email', flat=True)  

    # Create the email
    subject='Project Allocation Details'
    body='Please find attached the project allocation details for all students.'
    to=list(admin_emails)

    # send_email_report(to, subject, body, pdf)
    send_email_report.delay(to, subject, body, pdf)

    # Return a response to confirm that emails have been sent
    messages.success(request, "PDF with project allocation details has been sent to all admins."),
    return HttpResponseRedirect(reverse('create_cluster', args=(id,)))

