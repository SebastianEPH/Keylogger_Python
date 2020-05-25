echo off
color 04
pyinstaller --clean   --distpath "EXE Final" -F --windowed --icon icon.ico --version-file version.txt WindowsDefender.py
:cmd
pause null 
