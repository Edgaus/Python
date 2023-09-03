import os,sys  #Standard Python Libraries
import pandas as pd
import docx 
from docxtpl import DocxTemplate, InlineImage  # pip install docxtpl
import smtplib
from email.mime.text import MIMEText
from pathlib import Path




current_dir = os.getcwd() + '\chairs1.xlsx'
context = pd.read_excel(current_dir)


# Setup port number and server name
smtp_port = 587              # Standard secure SMTP port
smtp_server = "smtp.gmail.com"  # Google SMTP Server



# Set up the email lists
email_from = 'edgaus98@gmail.com'
# Define the password (better to reference externally)
pswd = '' 


# Define the email function (dont call it email!)


def sender_html(person, filename,i):

    # make a MIME object to define parts of the email
    msg = MIMEMultipart("alternatives")
    msg['From'] = '.'
    msg['To'] = person
    msg['Subject'] = ""
    subject = ""

    # Attach the body of the message

    html = Path("Text_correo.html").read_text()
    htmlPart = MIMEText(html, 'html' )
    msg.attach(htmlPart)
    
    # Open the file in python as a binary
    attachment= open(filename, 'rb')  # r for read and b for binary

    # Encode as base 64
    attachment_package = MIMEBase('application', 'octet-stream')
    attachment_package.set_payload((attachment).read())
    encoders.encode_base64(attachment_package)
    attachment_package.add_header('Content-Disposition', "attachment; filename= " + filename)
    msg.attach(attachment_package)
    
    # Cast as string
    text = msg.as_string()

    # Connect with the server
    print("Connecting to server...")
    TIE_server = smtplib.SMTP(smtp_server, smtp_port)
    TIE_server.starttls()
    TIE_server.login(email_from,pswd)
    print("Succesfully connected to server")
    print()


    # Send emails to "person" as list is iterated
    print(f"Sending email to: {person}...")
    TIE_server.sendmail(email_from, person, text)
    print(f"Email sent to: {person}")
    print()


    print(f'Correo número: {i+1}')
    print()

    # Close the port
    TIE_server.quit()



for i in range( 0, context.shape[0] ):
    

    extract = context.loc[i]
    person = extract['Nombres']
    receiver = extract['correo']

    version = 'Template.docx'
    doc = DocxTemplate(version)
    doc.render(extract)
    doc.save(f'Documents_Generated\Template Rendered {person}.docx')

    # Set the paths for the Word and PDF files
    word_path = f'Documents_Generated\Template Rendered {person}.docx'
    pdf_name = f"Documents_Generated\Acceptation Letter {person}.pdf"
 
    # Load the Word document using the docx library
    doc = docx.Document(word_path)
 
    # Save the Word document as a PDF using Microsoft Word
    word = comtypes.client.CreateObject("Word.Application")
    docx_path = os.path.abspath(word_path)
    pdf_path = os.path.abspath(pdf_name)

 
    pdf_format = 17  # PDF file format code
    word.Visible = False
    in_file = word.Documents.Open(docx_path)
    in_file.SaveAs(pdf_path, FileFormat=pdf_format)
    in_file.Close()
  
    # Quit Microsoft Word
    word.Quit()

    # Run the function
    sender_html(receiver,pdf_name,i)
