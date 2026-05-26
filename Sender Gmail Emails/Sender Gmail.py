import os
import sys
import time  # Necesario para la pausa antispam
import pandas as pd
import docx
from docxtpl import DocxTemplate
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import comtypes.client

current_dir = os.getcwd() 

# Leer el Excel
ruta_excel = os.path.join(current_dir, r'Datos\Test.xlsx')
context = pd.read_excel(ruta_excel)
context['Title'] = context['Title'].str.upper()
context['Authors'] = context['Authors'].str.replace("-", " ").str.upper()
context['autor_todos'] = context['autor_todos'].str.replace("-", " ").str.upper()

limit = context.shape[0]

# Configuración del servidor (Cuenta institucional en Google Workspace)
smtp_port = 587              
smtp_server = "smtp.gmail.com"           
# Set up the email lists
email_from = 'edgaus98@gmail.com'
# Define the password (better to reference externally)
pswd = 'ywqbodbjvxvmxtqy' 


# Función principal de envío
def sender_html(person, filename, i, pdf_name, mails, html_file_path):
    Name = person['Authors']

    for mail in mails:
        # 1. Contenedor principal
        msg = MIMEMultipart("mixed")
        msg['From'] = f'Sociedad Mexicana de Ciencia y Tecnología <{email_from}>'
        msg['To'] = mail
        msg['Subject'] = "Invitación a la 2da Parte del Curso: Fotoluminiscencia de Nanomateriales" 

        # 2. Sub-contenedor para Texto y HTML
        body_multipart = MIMEMultipart("alternative")
        msg.attach(body_multipart)

        # 3. Versión de Texto Plano (Para evitar filtros de Spam)
        texto_plano = f"""
        Estimado/a {Name},

        La Mesa Directiva del Capítulo Estudiantil y la Sociedad Mexicana de Ciencia y Tecnología 
        de Superficies y Materiales A.C.

        Les hace la mas cordial invitación a la segunda parte del curso de fotolomusicencia de nanomateriales importido por el Dr. Frank Güell de la Universidad de Barceñlona del 01 AL 05 de Junio, 2026 de 9:30 a 12:00 hrs en UPIITA-IPN

        Saludos cordiales,
        Comité Organizador
        """
        parte_texto = MIMEText(texto_plano, 'plain', 'utf-8') 

        # 4. Versión HTML (Para la vista del usuario)
        with open(html_file_path, 'r', encoding="utf-8") as file:
            html_text = file.read()
        
        # Reemplazar la variable en el HTML
        html_text = html_text.replace("{{ Nombre }}", str(Name))
        parte_html = MIMEText(html_text, 'html', 'utf-8')

        # 5. Adjuntar texto y HTML al sub-contenedor (El orden importa)
        body_multipart.attach(parte_texto)
        body_multipart.attach(parte_html)

        # 6. Adjuntar el PDF
        with open(filename, 'rb') as attachment:
            attachment_package = MIMEBase('application', 'octet-stream')
            attachment_package.set_payload((attachment).read())
        
        encoders.encode_base64(attachment_package)
        attachment_package.add_header('Content-Disposition', f"attachment; filename={pdf_name}")
        msg.attach(attachment_package)

        # 7. Enviar correo
        text = msg.as_string()
        print("Conectando al servidor...")
        
        with smtplib.SMTP(smtp_server, smtp_port) as TIE_server:
            TIE_server.starttls()
            TIE_server.login(email_from, pswd)
            
            print(f"Enviando correo a: {mail} (Autor: {Name})...")
            TIE_server.sendmail(email_from, mail, text)
            print("¡Correo enviado exitosamente!\n")
        
        # Pausa antispam vital de 3 segundos
        time.sleep(3)


# Bucle de generación y envío (He cambiado "1" por "limit" para que procese todo el Excel)
for i in range(limit):
    extract = context.loc[i]

    # Extraer correos (soporta múltiples separados por coma)
    

    # 1. Verificar si la celda de correo está vacía (NaN)
    if pd.isna(extract['email']):
        print(f"=== Fila {i+1}: Celda de correo vacía. Saltando... ===\n")
        continue  # Esto hace que salte a la siguiente fila del Excel

    # 2. Extraer correos de forma segura convirtiendo a texto primero
    authors_email = [email.strip() for email in str(extract['email']).split(',')]


    Submission_Id = extract['Submission_Id']

    # 1. Generar el Word desde el template
    version = os.path.join(current_dir, r'Datos\Template.docx')
    doc = DocxTemplate(version)
    doc.render(extract)
  
    # 2. Definir rutas para guardar
    word_path = os.path.join(current_dir, rf'Documents_Generated\Word\Acceptance Letter-{Submission_Id}.docx')
    pdf_path = os.path.join(current_dir, rf'Documents_Generated\PDF\Acceptance Letter-{Submission_Id}.pdf')
    pdf_name = f"Certificate Id-{Submission_Id}.pdf"

    # Guardar Word
    doc.save(word_path)

    # 3. Convertir Word a PDF usando Microsoft Word en segundo plano
    word = comtypes.client.CreateObject("Word.Application")
    docx_path_abs = os.path.abspath(word_path)
    pdf_path_abs = os.path.abspath(pdf_path)

    pdf_format = 17  
    word.Visible = False
    in_file = word.Documents.Open(docx_path_abs)
    in_file.SaveAs(pdf_path_abs, FileFormat=pdf_format)
    in_file.Close()
    word.Quit()

    # 4. Ruta directa al HTML limpio
    ruta_html = os.path.join(current_dir, r'Datos\html.txt')

    # 5. Ejecutar la función de envío
    sender_html(extract, pdf_path_abs, i, pdf_name, authors_email, ruta_html)
    
    print(f'=== Progreso: Fila {i+1} de {limit} completada ===\n')

print("Proceso finalizado con éxito.")