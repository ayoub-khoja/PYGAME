from PIL import Image
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load PNG image
png_path = os.path.join(script_dir, 'icon-desktop.png')
ico_path = os.path.join(script_dir, 'mario.ico')

# Open and convert
img = Image.open(png_path)

# Convert to RGBA if needed
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Create ICO with multiple sizes for best quality
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
img.save(ico_path, format='ICO', sizes=sizes)

print(f"✅ Icône créée: {ico_path}")
