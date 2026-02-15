"""
=== OUTIL DE CONVERSION D'ICONE ===
Convertit une image PNG en fichier ICO (icone Windows)
pour le raccourci du jeu sur le bureau.

Usage : python convertir_icone.py
"""

from PIL import Image
import os

# Repertoire du script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Chemin de l'image PNG source
png_path = os.path.join(script_dir, 'icon-desktop.png')
# Chemin du fichier ICO de sortie
ico_path = os.path.join(script_dir, 'mario.ico')

# Ouvrir et convertir l'image
img = Image.open(png_path)

# Convertir en RGBA si necessaire
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Creer le fichier ICO avec plusieurs tailles pour une meilleure qualite
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
img.save(ico_path, format='ICO', sizes=sizes)

print(f"Icone creee: {ico_path}")
