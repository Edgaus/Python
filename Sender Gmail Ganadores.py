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




current_dir = os.getcwd() + '\\Datos\\Sender Gmail Emails\\Ganadores_test.xlsx'
context = pd.read_excel(current_dir)
context['TRABAJO'] = context['TRABAJO'].str.upper()
context['AUTOR'] = context['AUTOR'].str.replace("-", " ").str.upper()
#context['autor_todos'] = context['autor_todos'].str.replace("-", " ").str.upper()


number_of_rows=context.shape[0]


# Setup port number and server name
smtp_port = 587              # Standard secure SMTP port
smtp_server = "smtp.gmail.com"  # Google SMTP Server



# Set up the email lists
email_from = 'edgaus98@gmail.com'
# Define the password (better to reference externally)
pswd = 'ywqbodbjvxvmxtqy' 


#email_from = 'smctsm.letters.and.certificates@gmail.com'
#pswd = 'nqjkhigvvukytwhc'

# Define the email function (dont call it email!)


def sender_html(person, filenames,i,pdf_names,mails):
    print("Preparing email...")
    Name = person['AUTOR']
    Trabajo = person['TRABAJO']

    cc = 'edgaus@outlook.com'
    print(f'Emails to send to: {mails}')

    for mail in mails:

        # make a MIME object to define parts of the email
        msg = MIMEMultipart("alternatives")
        msg['From'] = 'Capitulo Estudiantil SMCTMS'
        msg['To'] = mail
        msg['Cc'] = cc
        msg['Subject'] = "Constancia de participación en el Capítulo Estudiantil de la SMCTSM"

      

    # Attach the body of the message

        with open('Datos\\Sender Gmail Emails\\index_ganadores.html', 'r') as file:
            html_text = file.read()

        html_text += f"""

        
<div style="max-width: 700px; margin: 0 auto; font-family: Arial, Helvetica, sans-serif; color: #222;">


  <!-- Querido text -->
    <!-- SALUDO -->
        <tr>
          <td style="padding:10px 40px;text-align:center;color:#333333;">
            <p style="margin:0;font-size:24px;">
              <strong>Estimado ganador:</strong>
            </p>
          </td>
        </tr>
  
   <table cellpadding="0" cellspacing="0" align="center">
            <tr>
              <td style="
                background-color:#ffffff;
                border:3px solid #febc03;
                border-radius:30px;
                padding:12px 28px;
                text-align:center;
              ">         

     <span style="text-transform: uppercase; font-weight: bold; font-size: 17px; color: #333;">   {Name}</span>



              </td>
            </tr>
          </table>


  <!-- Body text -->
          <!-- MENSAJE PRINCIPAL -->
        <tr>
          <td style="padding:20px 40px;color:#333333;font-size:14px;line-height:1.6;text-align:center;">
          <p style="
            font-size:16px;
            line-height:1.6;
            margin:0 0 18px;
            color:black;
          ">              La Mesa Directiva del Capítulo Estudiantil de la
              <strong>Sociedad Mexicana de Ciencia y Tecnología de Superficies y Materiales A.C. (SMCTSM)</strong>
              se complace en felicitarte por haber obtenido el
              <strong>reconocimiento como GANADOR</strong>
              en la sesión de pósters.
            </p>
          </td>
        </tr>


  <!-- Work title -->
   <table cellpadding="0" cellspacing="0" align="center">
            <tr>
              <td style="
                background-color:#ffffff;
                border:3px solid #febc03;
                border-radius:30px;
                padding:12px 28px;
                text-align:center;
              ">         


     <span style="text-transform: uppercase; font-weight: bold; font-size: 17px; color: #333;">   {Trabajo}</span>



              </td>
            </tr>
          </table>

</div>
		</table>
	</td>
</tr>


<!-- BLUE BORDER -->
<tr>
  <td height="10" style="background-color:#febc03;"></td>
</tr>

<tr>
  <td style="padding:30px 20px;">
    <table width="100%" cellpadding="0" cellspacing="0">
      <tr>

        <!-- LEFT COLUMN (IMAGE) -->
        <td width="30%" align="center" valign="middle" style="padding:20px;">
          <a href="https://superficiesyvacio.smctsm.org.mx/index.php/SyV/about/submissions">
            <img src="https://scontent.fcul2-1.fna.fbcdn.net/v/t39.30808-6/600218897_872023225338050_1216382349286475066_n.jpg?stp=dst-jpg_s590x590_tt6&_nc_cat=101&ccb=1-7&_nc_sid=127cfc&_nc_ohc=MYraay7G5l0Q7kNvwE3QRp6&_nc_oc=AdliyZ30I3nvVcIXz52S-70IT1NyQsX3Mo8QAFTWT7UKTnSU6eEbzP8ki4I6kmqyGiS1HTcXsTFmSXbw25mZYfqq&_nc_zt=23&_nc_ht=scontent.fcul2-1.fna&_nc_gid=qDFDZkcj5BeoT7RyCmO1_A&oh=00_AfmwmK7MnanzEmrEy8hJ1FXZ6H_DcBeuRc6OOWDHDKb7PQ&oe=69469506"
                 width="160"
                 style="max-width:180px; display:block;"
                 alt="Libro de Memorias">
          </a>
        </td>

        <!-- RIGHT COLUMN (TEXT) -->
        <td width="70%" valign="middle" style="padding: 20px"; font-family:Arial, Helvetica, sans-serif; color:black;">
          
          <p style="
            font-size:16px;
            line-height:1.6;
            margin:0 0 18px;
            color:black;
          ">
           Te invitamos a enviar tu trabajo para su publicación en las memorias de la revista de la 
            <strong>Sociedad Mexicana de Materiales y Tecnología de Materriales y Superficies</strong>.
          </p>

          <!-- BUTTON -->
          <table cellpadding="0" cellspacing="0" align="center">
            <tr>
              <td style="
                background-color:#ffffff;
                border:3px solid #febc03;
                border-radius:30px;
                padding:12px 28px;
                text-align:center;
              ">
                <a href="https://superficiesyvacio.smctsm.org.mx/index.php/SyV/about/submissions"
                   style="
                     font-size:16px;
                     font-weight:bold;
                     color:black;
                     text-decoration:none;
                     font-family:Arial, Helvetica, sans-serif;
                   ">
                  Libro de Memorias
                </a>
              </td>
            </tr>
          </table>

        </td>
      </tr>
    </table>
  </td>
</tr>







<!-- BLUE BORDER -->
<tr>
  <td height="10" style="background-color:#febc03;"></td>
</tr>

<tr   >
  <td bgcolor="#eeeae4" style="background-color:#eeeae4;" align="center" style="margin:0; padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0" bgcolor="#eeeae4" style="background-color:#eeeae4;">
      <tr>
        <td align="center" style="
          padding:30px 20px;
          font-family:Arial, Helvetica, sans-serif;
          color:#333333;
          background-color:#eeeae4;
        ">

          <!-- CONTACT TEXT -->
          <p style="
            font-size:14px;
            font-weight:bold;
            margin:0 0 18px;
            text-align:center;
          ">
            Cualquier duda contactanos a traves de nuestras redes:
          </p>

          <!-- ICONS ROW -->
          <table cellpadding="0" cellspacing="0" bgcolor="#eeeae4">
            <tr>

              <td align="center" style="padding:0 8px;">
                <a href="https://www.facebook.com/profile.php?id=61583545131508&sk=followers">
                  <img src="https://scontent.fcul2-1.fna.fbcdn.net/v/t39.30808-6/598678071_871958992011140_3890330427023837439_n.jpg?_nc_cat=101&ccb=1-7&_nc_sid=127cfc&_nc_ohc=cI-M81D-l8kQ7kNvwGOZSXb&_nc_oc=Adk6G7w78bGk63UoD0Rm7OCldGTvtgLDI09jzO-frIPeoUSAjBHOSZ3H7bXo81b2izIcPrNnCR1P2sD15IB7dFmv&_nc_zt=23&_nc_ht=scontent.fcul2-1.fna&_nc_gid=7ujPhsQwjWn1pFyVnHGgNQ&oh=00_Afmjq8OxF63e22RzZ57CNeh1txGztEUFurOqh0VBRLguVw&oe=69466CC0"
                       height="60"
                       style="display:block;"
                       alt="Facebook">
                </a>
              </td>

              <td align="center" style="padding:0 8px;">
                <a href="https://site.smctsm.org.mx/jovenes-investigadores/">
                  <img src="https://scontent.fcul2-1.fna.fbcdn.net/v/t39.30808-6/600360742_871971052009934_1237548391976728549_n.jpg?_nc_cat=109&ccb=1-7&_nc_sid=127cfc&_nc_ohc=0gHS434i1IsQ7kNvwG7P_FN&_nc_oc=AdkMdvaYowsVc_bB_RrARh9IIEZqMP-jzvg3fp-HUQIqQs12e8EtVTaCn9bO3_uah1PiQM2EHjNRYpfia88oUwOt&_nc_zt=23&_nc_ht=scontent.fcul2-1.fna&_nc_gid=Ky-3V6iyyfLnpDfDGQM4jg&oh=00_Afn5qvxQDBpuFVI8ouq3tZt9OaQqYVYhtLJ_FA9blg1-0Q&oe=69466B2F"
                       height="60"
                       style="display:block;"
                       alt="Website">
                </a>
              </td>

              <td align="center" style="padding:0 8px;">
                <a href="https://www.google.com/maps/dir/24.7875568,-107.4122464/19.50887,-99.12632/">
                  <img src="https://scontent.fcul2-1.fna.fbcdn.net/v/t39.30808-6/597960258_871958985344474_8566074381747430605_n.jpg?_nc_cat=108&ccb=1-7&_nc_sid=127cfc&_nc_ohc=9Sh7lgI2-NQQ7kNvwE7_njX&_nc_oc=Admr0kttRP75r6v1Tdcm1hv4zE2Ujsgqqq_vqiiID9HOG4lNF9BSdUS6LiY3opl3T7CybQOqYT7dMCxW75gNg3e0&_nc_zt=23&_nc_ht=scontent.fcul2-1.fna&_nc_gid=7HwbbZvJRvuOK0p3QaG5lA&oh=00_AflsnGjB_kMrIzQnI22p8hnXntiNt4aAw-WqyEHp5uCqlA&oe=69466FB0"
                       height="60"
                       style="display:block;"
                       alt="Location">
                </a>
              </td>

              <td align="center" style="padding:0 8px;">
                <a href="mailto:contacto@smctsm.org.mx">
                  <img src="https://scontent.fcul2-1.fna.fbcdn.net/v/t39.30808-6/598880842_871958988677807_4097410557467909673_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=127cfc&_nc_ohc=3hLLlHmNHrAQ7kNvwFpM2Wu&_nc_oc=AdngqTdYtz7izer1BjyTcMmJtHJYICfCJLO1GWzO6ZQbAf2TAZBpnAZjZo5dsRXvU1Jp4Ekv__qfcDKJ5__VdUp6&_nc_zt=23&_nc_ht=scontent.fcul2-1.fna&_nc_gid=gQd5dUg4Fyx66VwN654qsg&oh=00_Afmxtn6EPIUzhRBZE0tCcNXFChOordDnaiCr0tnsTKVjNQ&oe=69465FEE"
                       height="60"
                       style="display:block;"
                       alt="Email">
                </a>
              </td>

            </tr>
          </table>

        </td>
      </tr>
    </table>
  </td>
</tr>
<tr>

<!-- BLUE BORDER -->
<tr>
  <td height="10" style="background-color:#febc03;"></td>
</tr>



	<td>
		<a href="https://site.smctsm.org.mx/2024-conference/">
			<img src="https://scontent.fcul2-1.fna.fbcdn.net/v/t39.30808-6/598811083_871893522017687_3986314631362548321_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=127cfc&_nc_ohc=IzOjusnufIQQ7kNvwGmyjUu&_nc_oc=AdkNQ8zkNcPjRag8CGeLkF7c7SD2dvNP6jXVpkhEsM7JFZdAHenMwdUAwSEWSzjeRiRsZJo_amXtxKfwX2llxJgT&_nc_zt=23&_nc_ht=scontent.fcul2-1.fna&_nc_gid=Qgzmz1fUQwmR78ZesEBkxQ&oh=00_AfkKhUhqIV6FAHC8xJanC400D-8YmKJTGRwAYWAkMAnIPw&oe=69463C70"  alt=""  width="600" 
			style="max-width: 100%;"> </a>
	</td>
</tr>
</body  >
</html>
"""

        
        with open('html_text.html', 'w', encoding="utf-8") as file:
            file.write(html_text)
        htmlPart = MIMEText(html_text, 'html' )
        msg.attach(htmlPart)
    

        for k in range(len(filenames)):
    # Open the file in python as a binary
          
          attachment= open(filenames[k], 'rb')  # r for read and b for binary

    # Encode as base 64
          attachment_package = MIMEBase('application', 'octet-stream')
          attachment_package.set_payload((attachment).read())
          encoders.encode_base64(attachment_package)
          attachment_package.add_header('Content-Disposition', "attachment; filename= " + pdf_names[k])
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

        mail = [mail, cc]

    # Send emails to "person" as list is iterated
        print(f"Sending email to: {Name}...")
        TIE_server.sendmail(email_from, mail, text)
        print(f"Email sent to: {Name}")
        print()


        print(f'Correo número: {i+1}')
        print()

    # Close the port
        TIE_server.quit()






def extraer_subcadena(cadena, caracter_inicio, caracter_fin):
    subcadenas = []
    while caracter_inicio in cadena and caracter_fin in cadena:
        inicio = cadena.index(caracter_inicio) + 1
        fin = cadena.index(caracter_fin, inicio)
        subcadenas.append(cadena[inicio:fin])
        cadena = cadena[fin + 1:]
    return subcadenas

limit = context.shape[0]   



for i in range(limit):


    extract = context.loc[i]
    name = extract['AUTOR']
    #authors_email= extraer_subcadena(extract['CORREO'], '<','>')
    authors_email = context.loc[i, 'CORREO']
    Submission_Id = extract['RESUMEN']
    Lugar = extract['LUGAR']
        

    version = 'Datos\\Sender Gmail Emails\\Constancia Capítulo Estudiantil SMCTSM Ganadores.docx'
    doc = DocxTemplate(version)
    doc.render(extract)

    # Set the paths for the Word and PDF files
    word_path = f'Datos\\Sender Gmail Emails\\Documents_Generated Ganadores\\Word\\Constancia Capítulo Estudiantil SMCTSM {Submission_Id}.docx'
    pdf_path = f'Datos\\Sender Gmail Emails\\Documents_Generated Ganadores\\PDF\\Constancia Capítulo Estudiantil SMCTSM {Submission_Id}.pdf'
    pdf_name = f"Constancia Ganador Capitulo Estudiantil SMCTSM {Lugar} Lugar.pdf"


    doc.save(word_path)

    second_pdf_path = f'Datos\\Sender Gmail Emails\\Documents_Generated\\PDF\\Constancia Capítulo Estudiantil SMCTSM {Submission_Id}.pdf'
    pdf_name_second = f"Constancia Capitulo Estudiantil SMCTSM {Submission_Id}.pdf"
 
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

    sender_html(extract,[pdf_path,second_pdf_path],i,[pdf_name,pdf_name_second],[authors_email])

    