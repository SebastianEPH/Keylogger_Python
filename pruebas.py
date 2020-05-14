import os

def CreateDir():
    try:  # Intenta crear la dirección
        os.makedirs('C:\\Users\\Public\\Security\\Windosdfdsfsdf\\')
        print("Exito al copiar")
    except :
        print("Error")
        
CreateDir()

    