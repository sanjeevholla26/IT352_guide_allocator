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

# from io import BytesIO
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import A4, inch
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
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

        # data = [
        #     ['Field', 'Details'],  # Table header
        #     ['Name', allocation.student.user.first_name+' '+allocation.student.user.last_name],  # Student's name
        #     ['Professor', allocation.current_allocation.user.first_name+' '+allocation.current_allocation.user.last_name],  # Professor name
        #     ['Email', allocation.student.user.email],  # Email address
        #     ['Date of Allocation', datetime.now().strftime("%Y-%m-%d")]  # Allocation date
        # ]
        # Create the event name heading
        event_heading_style = styles['Heading2']
        event_heading_style.alignment = 1  # Center alignment
        event_heading_style.fontSize = 18  # Smaller than the main and sub-headings
        event_heading_style.textColor = colors.darkblue  # Different color for distinction

        event_heading = Paragraph(f"Event: {allocation.event.event_name}", event_heading_style)

        data = [
            ['Field', 'Details'],  # Table header
            ['Name', allocation.student.user.first_name+' '+allocation.student.user.last_name],  # Student's name
            ['Professor', allocation.current_allocation.user.first_name+' '+allocation.current_allocation.user.last_name],  # Professor name
            ['Email', allocation.student.user.email],  # Email address
            ['Event', allocation.event.event_name],  # Event Name
            ['Date of Allocation', datetime.now().strftime("%Y-%m-%d")]  # Allocation date
        ]

        # # Update the elements list to include event name
        # elements.append(event_heading)  # Add event name heading
        # elements.append(Spacer(1, 0.3 * inch))  # Add space after event heading


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
    event_name = None
    batch = None
    branch = None

    for allocation in allocations:
        if allocation.event.id != id:
            continue

        if event_name is None:
            event_name = allocation.event.event_name
            batch = allocation.event.eligible_batch
            branch = allocation.event.eligible_branch

        if allocation.current_allocation.user not in prof_student_map:
            prof_student_map[allocation.current_allocation.user] = []

        prof_student_map[allocation.current_allocation.user].append(allocation.student)

    for prof in prof_student_map.keys():
        # Create a PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        # Get the default stylesheet and customize heading
        styles = getSampleStyleSheet()

        # Main heading
        main_heading_style = styles['Heading1']
        main_heading_style.alignment = 1
        main_heading_style.fontSize = 28
        main_heading_style.textColor = colors.black
        main_heading = Paragraph("National Institute of Technology Surathkal", main_heading_style)

        # Sub-heading
        sub_heading_style = styles['Heading2']
        sub_heading_style.alignment = 1
        sub_heading_style.fontSize = 22
        sub_heading_style.textColor = colors.black
        sub_heading = Paragraph("PROJECT ALLOCATION DETAILS", sub_heading_style)

        # Paragraph styles
        normal_style = styles['Normal']
        normal_style.fontSize = 12

        # Extract professor details
        prof_name = prof.get_full_name()
        prof_abbreviation = prof.faculty.abbreviation  # Assuming username is a short form
        
        # Create personalized greeting and event details
        greeting_paragraph = Paragraph(f"<br/>Dear Prof. {prof_name},", normal_style)
        event_details_paragraph = Paragraph(
            f"<b>Event:</b> {event_name}<br/>"
            f"<b>Batch:</b> {batch}<br/>"
            f"<b>Branch:</b> {branch}<br/><br/>",
            normal_style
        )
        intro_paragraph = Paragraph(f"Allocated Students for {prof_abbreviation} is:", normal_style)

        # Create table header
        data = [['Student Name', 'Branch', 'CGPA', 'Email']]
        for student in prof_student_map[prof]:
            data.append([student.user.get_full_name(), student.branch, student.cgpa, student.user.edu_email])

        # Define table
        table = Table(data, colWidths=[1.5 * inch] * 4)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        logo = Image(logo_path, width=1.6 * inch, height=1.2 * inch)

        # Build PDF structure
        elements = [
            logo,
            Spacer(1, 0.1 * inch),
            main_heading,
            Spacer(1, 0.2 * inch),
            sub_heading,
            Spacer(1, 0.2 * inch),
            greeting_paragraph,
            Spacer(1, 0.1 * inch),
            event_details_paragraph,
            intro_paragraph,
            Spacer(1, 0.3 * inch),
            table
        ]

        def add_page_border(canvas, doc):
            width, height = A4
            canvas.setStrokeColorRGB(0, 0, 0)
            canvas.setLineWidth(2)
            canvas.rect(20, 20, width - 40, height - 40)

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
    event_name = None
    batch = None
    branch = None

    # Prepare the PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()

    # Define heading styles
    main_heading_style = styles['Heading1']
    main_heading_style.alignment = 1
    main_heading_style.fontSize = 28
    main_heading_style.textColor = colors.black

    sub_heading_style = styles['Heading1']
    sub_heading_style.alignment = 1
    sub_heading_style.fontSize = 22
    sub_heading_style.textColor = colors.black

    normal_style = styles['Normal']
    normal_style.fontSize = 12

    # Create the main and sub-headings
    main_heading = Paragraph("National Institute of Technology Surathkal", main_heading_style)
    sub_heading = Paragraph("PROJECT ALLOCATION DETAILS", sub_heading_style)

    # Extract event details
    for allocation in allocations:
        if allocation.event.id == id:
            event_name = allocation.event.event_name
            batch = allocation.event.eligible_batch
            branch = allocation.event.eligible_branch
            break  # We only need these values once

    # Event details paragraph
    event_details = Paragraph(
        f"<br/><br/><br/><b>Event:</b> {event_name}<br/>"
        f"<b>Batch:</b> {batch}<br/>"
        f"<b>Branch:</b> {branch}<br/>",
        normal_style
    )

    # Prepare the data table for the PDF
    data = [['Student Username', 'Student Email', 'Allocated Faculty']]
    
    for allocation in allocations:
        if allocation.event.id != id:
            continue
        student_name = allocation.student.user.get_full_name()
        student_email = allocation.student.user.edu_email  
        allocated_faculty = allocation.current_allocation.user.username 
        data.append([student_name, student_email, allocated_faculty])

    # Define table
    table = Table(data, colWidths=[2 * inch, 3 * inch, 2 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    # Logo image
    logo = Image(logo_path, width=1.6 * inch, height=1.2 * inch)

    # Build the PDF structure
    elements = [
        logo,
        Spacer(1, 0.1 * inch),
        main_heading,
        Spacer(1, 0.2 * inch),
        sub_heading,
        Spacer(1, 0.2 * inch),
        event_details,  # Added event details here
        Spacer(1, 0.5 * inch),
        table
    ]

    def add_page_border(canvas, doc):
        width, height = A4
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(2)
        canvas.rect(20, 20, width - 40, height - 40)

    doc.build(elements, onFirstPage=add_page_border, onLaterPages=add_page_border)

    # Get the PDF content from the buffer
    pdf = buffer.getvalue()
    buffer.close()

    # Fetch all admin users
    admin_role = Role.objects.get(role_name="admin")  
    admin_emails = admin_role.users.values_list('edu_email', flat=True)

    # Create the email
    subject = 'Project Allocation Details'
    body = 'Please find attached the project allocation details for all students.'
    to = list(admin_emails)

    # Send email asynchronously
    send_email_report.delay(to, subject, body, pdf)

    # Return a response to confirm that emails have been sent
    messages.success(request, "PDF with project allocation details has been sent to all admins.")
    return HttpResponseRedirect(reverse('create_cluster', args=(id,)))
