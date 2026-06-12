import os
import sys
import time  # Necesario para la pausa antispam
import pandas as pd
from docxtpl import DocxTemplate
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import comtypes.client
import random  # Necesario para generar tiempos de espera aleatorios

current_dir = os.getcwd() 

# Leer el Excel
ruta_excel = os.path.join(current_dir, r'Datos\Lista.xlsx')
context = pd.read_excel(ruta_excel)

limit = context.shape[0]

# Configuración del servidor (Cuenta institucional en Google Workspace)
smtp_port = 587              
smtp_server = "smtp.gmail.com"  

email_from = 'edgaragustin.fcfm@uas.edu.mx'
pswd = 'evpzwaersahdmjyo' # Contraseña de aplicación

# Función principal de envío
def sender_html(person, filename, i, pdf_name, mails, html_file_path):
    # Aseguramos que los nombres se lean como texto, por si hay celdas vacías
    Name = str(person['Participante']).upper()
    

    for mail in mails:
        # 1. Contenedor principal simplificado a 'alternative'
        msg = MIMEMultipart("alternative")
        msg['From'] = f'Capítulo Estudiantil Jóvenes Investigadores <{email_from}>'
        msg['To'] = mail
        msg['Subject'] = "Constancia a la 2da Parte del Curso: Fotoluminiscencia de Nanomateriales" 

        # 2. Versión de Texto Plano (Ortografía corregida)
        texto_plano = f"""
        Estimado/a {Name},

        La Mesa Directiva del Capítulo Estudiantil y la Sociedad Mexicana de Ciencia y Tecnología 
        de Superficies y Materiales A.C.

        Les hace la más cordial invitación a la segunda parte del curso de Fotoluminiscencia de Nanomateriales impartido por el Dr. Frank Güell de la Universidad de Barcelona, del 01 al 05 de junio de 2026, de 9:30 a 12:00 hrs en UPIITA-IPN.

        Saludos cordiales,
        Comité Organizador
        """
        parte_texto = MIMEText(texto_plano, 'plain', 'utf-8') 

        # 3. Versión HTML (Para la vista del usuario)
        with open(html_file_path, 'r', encoding="utf-8") as file:
            html_text = file.read()
        
        # Reemplazar las variables en el HTML
        html_text = html_text.replace("{{ Participante }}", Name)
        parte_html = MIMEText(html_text, 'html', 'utf-8')

        # 4. Adjuntar texto y HTML al contenedor principal (El texto SIEMPRE va primero)
        msg.attach(parte_texto)
        msg.attach(parte_html)


        # 6. Adjuntar el PDF
        with open(filename, 'rb') as attachment:
            attachment_package = MIMEBase('application', 'octet-stream')
            attachment_package.set_payload((attachment).read())
        
        encoders.encode_base64(attachment_package)
        attachment_package.add_header('Content-Disposition', f"attachment; filename={pdf_name}")
        msg.attach(attachment_package)


        # 5. Enviar correo
        text = msg.as_string()
        print("Conectando al servidor...")  



        
        with smtplib.SMTP(smtp_server, smtp_port) as TIE_server:
            TIE_server.starttls()   
            TIE_server.login(email_from, pswd)  
            
            print(f"Enviando correo a: {mail} (Autor: {Name})...")
            TIE_server.sendmail(email_from, mail, text)
            print("¡Correo enviado exitosamente!\n")
        
        # 6. Pausa antispam con comportamiento "humano" (entre 6 y 12 segundos)
        tiempo_espera = random.uniform(6, 12)
        print(f"Esperando {tiempo_espera:.1f} segundos para proteger la cuenta...\n")
        time.sleep(tiempo_espera)


# Bucle de generación y envío
for i in range(limit):
    extract = context.loc[i]
    

    if extract['Constancia'] == 'Sí':
       # 1. Generar el Word desde el template
        version = os.path.join(current_dir, r'Datos\Template.docx')
        doc = DocxTemplate(version)
        doc.render(extract)
  
        Submission_Id = extract['Participante'][:3].upper() + str(i+1).zfill(3)  # ID único basado en el nombre y número de fila

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






        # 1. Verificar si la celda de correo está vacía (NaN)
        if pd.isna(extract['Correo']):
            print(f"=== Fila {i+1}: Celda de correo vacía. Saltando... ===\n")
            continue  

    # 2. Extraer correos de forma segura
        authors_email = [email.strip() for email in str(extract['Correo']).split(',')]

    # 3. Ruta directa al archivo que contiene el diseño
        ruta_html = os.path.join(current_dir, r'Datos\html.txt')

    # 4. Ejecutar la función de envío
        sender_html(extract, pdf_path_abs, i, pdf_name, authors_email, ruta_html)
    
        print(f'=== Progreso: Fila {i+1} de {limit} completada ===\n')

        print("Proceso finalizado con éxito.")
    else:
        print(f"=== Fila {i+1}: No se requiere constancia. Saltando... ===\n")