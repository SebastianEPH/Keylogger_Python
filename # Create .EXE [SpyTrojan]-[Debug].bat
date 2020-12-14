echo off
color cf
title Run script - Py to EXE [DEBUG]
pyinstaller --clean   --distpath "[DEBUG]" -F --icon "icon_SpyTrojan.ico" --version-file info_exe_SpyTrojan.txt SpyTrojan.py
:cmd
pause null 
