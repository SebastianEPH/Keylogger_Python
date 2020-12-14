echo off
color a0
title Run script - Py to EXE [Release]
pyinstaller --clean   --distpath "[RELEASE]" -F --windowed --icon "icon_infection_file.ico" --version-file info_exe_InfectionFile.txt InfectionFile.py
:cmd
pause null 
