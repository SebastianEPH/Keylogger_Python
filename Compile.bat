echo off
pyinstaller --clean   --distpath "CompiladoEXE" -F --windowed --icon icon.ico --version-file version.txt WindowsDefender.py
:cmd
pause null 
