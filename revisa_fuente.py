import matplotlib.font_manager as fm
from pathlib import Path

# Registrar fuentes desde la carpeta
fonts_dir = Path("data/raw/fonts")
for font_path in list(fonts_dir.glob("*.otf")) + list(fonts_dir.glob("*.ttf")):
    fm.fontManager.addfont(str(font_path))
    print(f"Registrada: {font_path.name}")

# Ahora buscar
print("\n--- Fuentes Museo encontradas ---")
for f in fm.fontManager.ttflist:
    if "Museo" in f.name:
        print(f"nombre: {f.name!r}  peso: {f.weight}  archivo: {Path(f.fname).name}")