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
ruta_excel = os.path.join(current_dir, r'Datos\Full.xlsx')
context = pd.read_excel(ruta_excel)

limit = context.shape[0]

# Configuración del servidor (Cuenta institucional en Google Workspace)
smtp_port = 587                 
smtp_server = "smtp.gmail.com"   


# Set up the email lists
email_from = 'edgaragustin.fcfm@uas.edu.mx'
pswd = 'evpzwaersahdmjyo' # Contraseña de aplicació

# Función principal de envío
def sender_html(person, mails, html_file_path):
    Name = str(person['Nombre'])
    LastName = str(person['Apellido'])

    for mail in mails:
        # 1. Contenedor principal
        msg = MIMEMultipart("mixed")
        msg['From'] = f'Capítulo Estudiantil Jóvenes Investigadores <{email_from}>'
        msg['To'] = mail
        msg['Subject'] = "Revista Superficies y Vacío" 

        # 2. Sub-contenedor para Texto y HTML
        body_multipart = MIMEMultipart("alternative")
        msg.attach(body_multipart)

        # 3. Versión de Texto Plano (Para evitar filtros de Spam)
        texto_plano = f"""
        Estimado/a {Name} {LastName},

        La Mesa Directiva del Capítulo Estudiantil y la Sociedad Mexicana de Ciencia y Tecnología 
        de Superficies y Materiales A.C.

        Se complace en informarle que la revista "Superficies y Vacío" ha sido admitida en el SNPCyH 2026 coordinado por la SECIHTI.
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
for i in range(186, limit):
    extract = context.loc[i]

    # Extraer correos (soporta múltiples separados por coma)
    

    # 1. Verificar si la celda de correo está vacía (NaN)
    if pd.isna(extract['email']):
        print(f"=== Fila {i+1}: Celda de correo vacía. Saltando... ===\n")
        continue  # Esto hace que salte a la siguiente fila del Excel

    # 2. Extraer correos de forma segura convirtiendo a texto primero
    authors_email = [email.strip() for email in str(extract['email']).split(',')]

    # 4. Ruta directa al HTML limpio
    ruta_html = os.path.join(current_dir, r'Datos\html.txt')

    # 5. Ejecutar la función de envío
    sender_html(extract, authors_email, ruta_html)

    print(f'=== Progreso: Fila {i+1} de {limit} completada ===\n')

print("Proceso finalizado con éxito.")