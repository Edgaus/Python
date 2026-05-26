import os
import time  
import random  # Librería añadida para las pausas aleatorias
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

current_dir = os.getcwd() 

# Leer el Excel
ruta_excel = os.path.join(current_dir, r'Datos\Lista de Invitados.xlsx')
context = pd.read_excel(ruta_excel)

limit = context.shape[0]

# Configuración del servidor (Cuenta institucional en Google Workspace)
smtp_port = 587              
smtp_server = "smtp.gmail.com"  

email_from = 'edgaragustin.fcfm@uas.edu.mx'
pswd = 'evpzwaersahdmjyo' # Contraseña de aplicación

# Función principal de envío
def sender_html(person, mails, html_file_path):
    # Aseguramos que los nombres se lean como texto, por si hay celdas vacías
    Name = str(person['Nombre'])
    Apellido = str(person['Apellido'])

    for mail in mails:
        # 1. Contenedor principal simplificado a 'alternative'
        msg = MIMEMultipart("alternative")
        msg['From'] = f'Capítulo Estudiantil Jóvenes Investigadores <{email_from}>'
        msg['To'] = mail
        msg['Subject'] = "Invitación a la 2da Parte del Curso: Fotoluminiscencia de Nanomateriales" 

        # 2. Versión de Texto Plano (Ortografía corregida)
        texto_plano = f"""
        Estimado/a {Name} {Apellido},

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
        html_text = html_text.replace("{{ Nombre }}", Name).replace("{{ Apellido }}", Apellido)
        parte_html = MIMEText(html_text, 'html', 'utf-8')

        # 4. Adjuntar texto y HTML al contenedor principal (El texto SIEMPRE va primero)
        msg.attach(parte_texto)
        msg.attach(parte_html)

        # 5. Enviar correo
        text = msg.as_string()
        print("Conectando al servidor...")  
        
        with smtplib.SMTP(smtp_server, smtp_port) as TIE_server:
            TIE_server.starttls()   
            TIE_server.login(email_from, pswd)  
            
            print(f"Enviando correo a: {mail} (Autor: {Name} {Apellido})...")
            TIE_server.sendmail(email_from, mail, text)
            print("¡Correo enviado exitosamente!\n")
        
        # 6. Pausa antispam con comportamiento "humano" (entre 6 y 12 segundos)
        tiempo_espera = random.uniform(6, 12)
        print(f"Esperando {tiempo_espera:.1f} segundos para proteger la cuenta...\n")
        time.sleep(tiempo_espera)


# Bucle de generación y envío
for i in range(limit):
    extract = context.loc[i]

    # 1. Verificar si la celda de correo está vacía (NaN)
    if pd.isna(extract['email']):
        print(f"=== Fila {i+1}: Celda de correo vacía. Saltando... ===\n")
        continue  

    # 2. Extraer correos de forma segura
    authors_email = [email.strip() for email in str(extract['email']).split(',')]

    # 3. Ruta directa al archivo que contiene el diseño
    ruta_html = os.path.join(current_dir, r'Datos\html.txt')

    # 4. Ejecutar la función de envío
    sender_html(extract, authors_email, ruta_html)
    
    print(f'=== Progreso: Fila {i+1} de {limit} completada ===\n')

print("Proceso finalizado con éxito.")