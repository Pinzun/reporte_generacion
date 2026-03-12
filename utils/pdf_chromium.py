from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright


def render_html_to_png(
    template_dir: Path,
    template_name: str,
    context: dict,
    output_png: Path,
    output_html: Path,
    dpi: int = 300,
):
    """
    Renderiza HTML con Jinja2 y lo exporta a PNG usando Chromium (Playwright).

    Estrategia:
    - viewport en tamaño CSS real de A4
    - device_scale_factor para aumentar resolución final

    A4 portrait:
    - CSS px aprox: 794 x 1123
    - 300 dpi final aprox: 2480 x 3508
    """
    template_dir = template_dir.resolve()
    output_png = output_png.resolve()
    output_html = output_html.resolve()

    output_png.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template(template_name)
    html_str = template.render(**context)

    # Guardar HTML renderizado para debug
    tmp_html = output_html.with_suffix(".html")
    tmp_html.write_text(html_str, encoding="utf-8")

    # =========================
    # A4 portrait en CSS px (~96 dpi)
    # =========================
    css_width_px = 794
    css_height_px = 1123

    # Escala para aproximar resolución final
    scale_factor = dpi / 96

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page(
            viewport={"width": css_width_px, "height": css_height_px},
            device_scale_factor=scale_factor,
        )

        page.goto(tmp_html.as_uri(), wait_until="networkidle")
        page.emulate_media(media="screen")

        # Captura exacta del contenedor .page
        page.locator(".page").screenshot(
            path=str(output_png),
            type="png",
        )

        browser.close()

    return output_png, tmp_html