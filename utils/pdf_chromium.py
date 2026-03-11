from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright


def render_html_to_pdf(
    template_dir: Path,
    template_name: str,
    context: dict,
    output_pdf: Path,
    base_dir: Path,
):
    """
    Renderiza HTML con Jinja2 y lo imprime a PDF usando Chromium (Playwright).
    - template_dir: carpeta templates/
    - template_name: "reporte.html"
    - context: variables Jinja2
    - output_pdf: ruta destino del PDF
    - base_dir: raíz del proyecto (para base_url)
    """
    template_dir = template_dir.resolve()
    output_pdf = output_pdf.resolve()
    base_dir = base_dir.resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template(template_name)
    html_str = template.render(**context)

    # Guardar HTML temporal al lado del PDF (útil para debug y rutas relativas)
    tmp_html = output_pdf.with_suffix(".html")
    tmp_html.write_text(html_str, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        page = browser.new_page()

        # Cargar el HTML desde archivo para que rutas relativas funcionen
        page.goto(tmp_html.as_uri(), wait_until="networkidle")

        # Exportar a PDF
        page.pdf(
            path=str(output_pdf),
            format="A4",
            landscape=True,
            print_background=True,
            margin={"top": "18mm", "right": "14mm", "bottom": "18mm", "left": "14mm"},
        )

        browser.close()

    return output_pdf, tmp_html