# utils/inserta_graficos_ppt.py
from pptx import Presentation
from pathlib import Path


# ── Mapeo placeholder → archivo generado por generar_graficas() ──────────────
PLACEHOLDER_IMG_MAP = {
    "img_cmg":                      "cmg.png",
    "img_dia_tipico":               "gx_tipico.png",
    "img_spread":                   "spread_cmg.png",
    "img_inyecciones_vertimientos": "inyec_vert.png",
    "img_inyeccion_bess":           "inyecciones_bess.png",
    "img_evolucion_vertimientos":   "evolucion_vertimiento.png",
}

# ── Dimensiones exactas extraídas del PPT (pulgadas) ─────────────────────────
PLACEHOLDER_DIMS = {
    "img_cmg":                        (11.16, 5.55),  # Slide 1
    "img_spread":                     (5.95, 4.41),   # Slide 2
    "img_inyeccion_bess":             (6.02, 4.15),   # Slide 2
    "img_evolucion_vertimientos":     (6.02, 3.97),   # Slide 2
    "img_dia_tipico":                 (10.74, 5.95),  # Slide 3
    "img_inyecciones_vertimientos":   (5.25, 4.94),   # Slide 3
}

# DPI para todos los gráficos
TARGET_DPI = 150  
def get_figsize(placeholder_name: str, dpi: int = TARGET_DPI) -> tuple[float, float]:
    """
    Retorna (width_in, height_in) exactas del placeholder.
    Con este figsize + el dpi indicado, la imagen sale en los píxeles
    exactos del espacio en PPT — sin escalado.
    """
    dims = PLACEHOLDER_DIMS.get(placeholder_name)
    if dims is None:
        raise ValueError(f"'{placeholder_name}' no tiene dimensiones registradas.")
    return dims


def _buscar_shape_recursivo(shapes, nombre: str):
    """Busca un shape por nombre incluyendo dentro de grupos."""
    for shape in shapes:
        if shape.name == nombre:
            return shape
        if shape.shape_type == 6:  # MSO_SHAPE_TYPE.GROUP = 6
            encontrado = _buscar_shape_recursivo(shape.shapes, nombre)
            if encontrado:
                return encontrado
    return None


def insertar_graficos_ppt(ppt_path: Path, img_dir: Path, margen: float = 0.5) -> None:
    """
    margen: margen interior en pulgadas por cada lado (default 0.15 in)
    """
    from pptx.util import Inches

    ppt_path = Path(ppt_path)
    img_dir  = Path(img_dir)
    prs      = Presentation(ppt_path)
    margen_emu = int(margen * 914400)  # pulgadas → EMUs

    for slide_num, slide in enumerate(prs.slides, 1):
        for nombre, archivo in PLACEHOLDER_IMG_MAP.items():

            shape = _buscar_shape_recursivo(slide.shapes, nombre)
            if shape is None:
                continue

            img_file = img_dir / archivo
            if not img_file.exists():
                print(f"  ⚠️  Imagen no encontrada: {archivo} (slide {slide_num})")
                continue

            # Aplicar margen interior — reduce tamaño y desplaza para centrar
            slide.shapes.add_picture(
                str(img_file),
                left=shape.left     + margen_emu,
                top=shape.top       + margen_emu,
                width=shape.width   - margen_emu * 2,
                height=shape.height - margen_emu * 2,
            )
            print(f"  ✅ {nombre} → {archivo} (slide {slide_num})")

    prs.save(ppt_path)
    print(f"\nPPT guardado: {ppt_path}")