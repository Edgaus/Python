import os,sys  #Standard Python Libraries
import pandas as pd
import docx 
from docxtpl import DocxTemplate, InlineImage  # pip install docxtpl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import comtypes.client




current_dir = os.getcwd() + '\Datos\Sender Gmail Emails\Practica.xlsx'
context = pd.read_excel(current_dir)
context['Submitter_first_name'] = context['Submitter_first_name'].str.title()
context['Submitter_last_name'] = context['Submitter_last_name'].str.title()


# Setup port number and server name
smtp_port = 587              # Standard secure SMTP port
smtp_server = "smtp.gmail.com"  # Google SMTP Server



# Set up the email lists
email_from = 'edgaus98@gmail.com'
# Define the password (better to reference externally)
pswd = 'ywqbodbjvxvmxtqy' 


# Define the email function (dont call it email!)


def sender_html(person, filename,i,pdf_name):

    first = person['Submitter_first_name']
    last = person['Submitter_last_name']
    Trabajo = person['Title']
    mail = person['Submitter_email']

    # make a MIME object to define parts of the email
    msg = MIMEMultipart("alternatives")
    msg['From'] = 'Sociedad Mexicana de Ciencia y Tencologia de Superficies y Materiales A.C.'
    msg['To'] = mail
    msg['Subject'] = "Certificate of contribution at the XVI-International Conference on Surfaces Materials and Vacuum"
 

    # Attach the body of the message

    text = f'''
    We greatly appreciate your participation in the XVI International Conference on Surfaces, Materials and Vacuum 2023, with the abstract entitled:
    <b>{Trabajo} </b>
    The Certificate of presentation of this contribution has been attached to this email.
    On behalf of the Organizing Committee,
    Dr. Cristo Manuel Yee Rendón
    President of the SMCTSM
    <img src=https://site.smctsm.org.mx/wp-content/uploads/2023/08/cropped-cropped-logoT-90x90.png class='back'>
    '''

    
    with open('Datos\Sender Gmail Emails\example.txt', 'r') as file:
        html_text = file.read()

    html_text +=f'<h3>Dear {first} {last}</h3>\n'

    for line in text.split('\n'):
        html_text += f'<p style="font-family: Arial, sans-serif; color: #555555; line-height: 1.6;">{line}</p>\n'

    html_text += '</td>\n</tr>\n</table>\n</td>\n</tr>\n</table>\n</td>\n</body>\n</html>\n'

    with open('html_text.html', 'w', encoding="utf-8") as file:
        file.write(html_text)
    htmlPart = MIMEText(html_text, 'html' )
    msg.attach(htmlPart)
    
    # Open the file in python as a binary
    attachment= open(filename, 'rb')  # r for read and b for binary

    # Encode as base 64
    attachment_package = MIMEBase('application', 'octet-stream')
    attachment_package.set_payload((attachment).read())
    encoders.encode_base64(attachment_package)
    attachment_package.add_header('Content-Disposition', "attachment; filename= " + pdf_name)
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
    print(f"Sending email to: {first}...")
    TIE_server.sendmail(email_from, mail, text)
    print(f"Email sent to: {first}")
    print()


    print(f'Correo número: {i+1}')
    print()

    # Close the port
    TIE_server.quit()

limit = context.shape[0]

for i in range( 0, 2 ):
    

    extract = context.loc[i]



    person = extract['Submitter_first_name'] + " " + extract['Submitter_last_name']
    receiver = extract['Submitter_email']
    Submission_Id = extract['Submission_Id']

    version = 'Datos\Sender Gmail Emails\Template.docx'
    doc = DocxTemplate(version)
    doc.render(extract)

    # Set the paths for the Word and PDF files
    word_path = f'Datos\Sender Gmail Emails\Documents_Generated\Word\Template Rendered {person}-{Submission_Id}.docx'
    pdf_path = f'Datos\Sender Gmail Emails\Documents_Generated\PDF\Constance {person}-{Submission_Id}.pdf'
    pdf_name = f"Certificate Id-{Submission_Id}.pdf"


    doc.save(word_path)

    # Set the paths for the Word and PDF files
    word_path = f'Datos\Sender Gmail Emails\Documents_Generated\Word\Template Rendered {person}-{Submission_Id}.docx'
    pdf_path = f'Datos\Sender Gmail Emails\Documents_Generated\PDF\Constance {person}-{Submission_Id}.pdf'
    pdf_name = f"Certificate Id-{Submission_Id}.pdf"
 
    # Load the Word document using the docx library
    doc = docx.Document(word_path)
 
    # Save the Word document as a PDF using Microsoft Word
    word = comtypes.client.CreateObject("Word.Application")
    docx_path = os.path.abspath(word_path)
    pdf_path = os.path.abspath(pdf_path)

 
    pdf_format = 17  # PDF file format code
    word.Visible = False
    in_file = word.Documents.Open(docx_path)
    in_file.SaveAs(pdf_path, FileFormat=pdf_format)
    in_file.Close()
  
    # Quit Microsoft Word
    word.Quit()

    # Run the function
    #sender_html(extract,pdf_path,i,pdf_name)
