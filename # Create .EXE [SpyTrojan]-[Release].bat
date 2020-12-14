echo off
color a0
title Run script - Py to EXE [Release]
pyinstaller --clean   --distpath "[RELEASE]" -F --windowed --icon "icon_SpyTrojan.ico" --version-file info_exe_SpyTrojan.txt SpyTrojan.py
:cmd
pause null 
