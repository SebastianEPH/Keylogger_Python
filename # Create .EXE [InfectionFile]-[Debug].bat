echo off
color cf
title Run script - Py to EXE [DEBUG]
pyinstaller --clean   --distpath "[DEBUG]" -F --icon "icon_infection_file.ico" --version-file info_exe_InfectionFile.txt InfectionFile.py
:cmd
pause null 
