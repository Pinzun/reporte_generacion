import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import geopandas as gpd
# NUEVO: seaborn para estética
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
import numpy as np


SHP_REGIONES = r"C:\Users\pinzunza\OneDrive - Ministerio de Energia\Escritorio\escritorio desrodenado\capas\Comunas\COMUNAS_NACIONAL.shp"
BAR_POINTS = {
    "Barra crucero 200kV": {
        "lon": -69.5677773900849,
        "lat": -22.27773471974709
    },
    "Barra Pan de Azucar 220kV": {
        "lon": -71.100,
        "lat": -29.900
    },
    "Barra Quillota 220kV": {
        "lon": -71.260,
        "lat": -32.880
    },
    "Barra Alto Jahuel 500kV": {
        "lon": -70.630,
        "lat": -33.720
    },
    "Barra Puerto Montt 220kV": {
        "lon": -72.940,
        "lat": -41.470
    }
    ,
    "Barra Charrua 500kV": {
        "lon": -72.940,
        "lat": -41.470
    }
}


def _fmt_thousands(x, pos):
    try:
        return f"{x:,.0f}".replace(",", ".")
    except Exception:
        return str(x)


def _guardar_fig(fig, path, dpi=130):
    ext = os.path.splitext(path)[1].lower()
    """
    Guardado pensado para HTML->PDF (Chromium):
    - DPI moderado (no necesitas 220+)
    - tight_layout para reducir blancos, pero sin inflar tanto el canvas
    """
    try:
        fig.tight_layout()
    except Exception:
        pass

    if ext == ".svg":
        fig.savefig(path, format="svg", bbox_inches="tight")
    else:
        fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


def _render_table_image(df, title, outpath, dpi=150, max_rows=25):
    """
    Renderiza un DataFrame como imagen usando matplotlib.table.
    Ajustado para que NO salga gigante en HTML/PDF.
    - max_rows menor
    - tamaños acotados
    - dpi moderado
    """
    df_show = df.copy()

    for col in df_show.columns:
        if pd.api.types.is_numeric_dtype(df_show[col]):
            df_show[col] = df_show[col].map(
                lambda v: f"{v:,.0f}".replace(",", ".") if pd.notnull(v) else ""
            )

    if len(df_show) > max_rows:
        df_show = df_show.head(max_rows)

    nrows, ncols = df_show.shape
    fig_w = min(12, max(8.5, ncols * 1.25))
    fig_h = min(8.0, max(2.8, 0.28 * (nrows + 2)))

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=8)

    table = ax.table(
        cellText=df_show.values,
        colLabels=df_show.columns.tolist(),
        loc="center",
        cellLoc="center",
        colLoc="center",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1, 1.05)

    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor("#E6E6E6")
            cell.set_text_props(weight="bold")
        else:
            cell.set_facecolor("#FFFFFF" if r % 2 else "#F7F7F7")

    _guardar_fig(fig, outpath, dpi=dpi)

def generar_mapa_regiones(shp_path, target_crs="EPSG:32719"):
    import geopandas as gpd

    CUT_COM_EXCLUIR = [5201, 5104]
    REGIONES_INCLUIR = [15, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 16, 13]

    gdf = gpd.read_file(shp_path)

    gdf["CUT_COM"] = gdf["CUT_COM"].astype(str).str.strip().astype(int)
    gdf = gdf.loc[~gdf["CUT_COM"].isin(CUT_COM_EXCLUIR)].copy()

    gdf["CUT_REG"] = gdf["CUT_REG"].astype(str).str.strip().astype(int)

    gdf = gdf.dissolve(by="CUT_REG", aggfunc="first").reset_index()

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326", allow_override=True)

    gdf = gdf.to_crs(target_crs)

    gdf = gdf.loc[gdf["CUT_REG"].isin(REGIONES_INCLUIR)].copy()
    gdf = gdf.sort_values("CUT_REG").reset_index(drop=True)

    return gdf

def graficar_cmg_con_mapa(df_cmg, gdf_reg, bar_points, out_path, dpi=300):


    df_c = df_cmg.copy()
    df_c["fecha_version"] = pd.to_datetime(df_c["fecha_version"], errors="coerce")
    df_c = df_c.sort_values("fecha_version")

    fig, ax = plt.subplots(figsize=(14, 7))

    # Inset del mapa: [left, bottom, width, height] en coords de figura (0..1)
    # Ajusta estos números si lo quieres más grande/arriba/abajo
    ax_map = fig.add_axes([0.85, 0.35, 0.26, 0.6])
    ax_map.grid(False)

    # -------------------------
    # Paleta fija por barra
    # -------------------------
    barras = sorted(df_c["nombre_cmg"].dropna().unique())
    palette = sns.color_palette("pastel", n_colors=len(barras))
    color_map = dict(zip(barras, palette))

    # -------------------------
    # Lineplot (sin leyenda auto)
    # -------------------------
    sns.lineplot(
        data=df_c,
        x="fecha_version",
        y="CMG_PESO_KWH",
        hue="nombre_cmg",
        hue_order=barras,
        palette=color_map,
        ax=ax,
        linewidth=2.5,
        estimator=None,
        legend=False,
    )

    ax.set_title("Costo Marginal promedio por mes ($/kWh)", fontsize=16, fontweight="bold")
    ax.set_xlabel("Fecha", fontsize=14)
    ax.set_ylabel("CMG ($/kWh)", fontsize=14)
    # Grid SOLO en Y (más útil para lectura) — luego lo extendemos a figura
    ax.grid(False)
    ax.yaxis.grid(True, alpha=0.18, linewidth=0.8)
    ax.xaxis.grid(False)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    sns.despine(ax=ax)

    # -------------------------
    # Mapa fondo
    # -------------------------
    # Orden norte -> sur por CUT_REG
    gdf_reg_plot = gdf_reg.sort_values("CUT_REG").reset_index(drop=True)

    # Gradiente pastel naranja -> azul
    PASTEL_ORANGE = "#F6B38E"
    PASTEL_BLUE   = "#8EC5FF"

    cmap = LinearSegmentedColormap.from_list(
        "pastel_orange_blue",
        [PASTEL_ORANGE, PASTEL_BLUE]
    )

    colors = [cmap(i) for i in np.linspace(0, 1, len(gdf_reg_plot))]
    gdf_reg_plot["_color"] = colors

    gdf_reg_plot.plot(
        ax=ax_map,
        color=gdf_reg_plot["_color"],
        edgecolor="white",
        linewidth=0.8,
        zorder=1
    )
    # -------------------------
    # Puntos (mismo color que línea)
    # -------------------------
    rows = []
    for b in barras:
        if b in bar_points:
            rows.append({
                "nombre_cmg": b,
                "lon": bar_points[b]["lon"],
                "lat": bar_points[b]["lat"]
            })

    if rows:
        pts = gpd.GeoDataFrame(
            rows,
            geometry=gpd.points_from_xy(
                [r["lon"] for r in rows],
                [r["lat"] for r in rows]
            ),
            crs="EPSG:4326"
        ).to_crs(gdf_reg.crs)

        for _, r in pts.iterrows():
            b = r["nombre_cmg"]
            ax_map.scatter(
                r.geometry.x,
                r.geometry.y,
                s=60,
                marker="o",
                color=color_map[b],
                edgecolor="white",
                linewidth=0.8,
                zorder=5
            )

    # Zoom mapa
    minx, miny, maxx, maxy = gdf_reg.total_bounds
    dx, dy = maxx - minx, maxy - miny
    ax_map.set_xlim(minx - 0.1*dx, maxx + 0.1*dx)
    ax_map.set_ylim(miny - 0.03*dy, maxy + 0.03*dy)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")
    # Fondo idéntico entre subplots (mejora integración visual)
    ax_map.set_facecolor(ax.get_facecolor())
    ax_map.patch.set_alpha(1.0)

    for spine in ax_map.spines.values():
        spine.set_visible(True)
        spine.set_color("#D0D5DD")
        spine.set_linewidth(0.9)
    # -------------------------
    # Leyenda unificada
    # -------------------------
    handles = [
        Line2D(
            [0], [0],
            color=color_map[b],
            linewidth=2.5,
            marker="o",
            markersize=7,
            markerfacecolor=color_map[b],
            markeredgecolor="white",
            label=b
        )
        for b in barras
    ]

    leg = ax.legend(
        handles=handles,
        title="Nombre barra CMG",
        loc="upper left",
        fontsize=12,
        title_fontsize=14,
        frameon=True
    )
    leg.get_frame().set_alpha(0.9)

    _guardar_fig(fig, out_path, dpi=dpi)
    plt.close(fig)


def generar_graficas(df_total, df_all, df_maximos, df_max_acumulados, df_cmg, outdir="outputs", dpi=130):
    os.makedirs(outdir, exist_ok=True)

    # ==========================================================
    # Seaborn theme (moderno y limpio)
    # ==========================================================
    sns.set_theme(
        style="whitegrid",
        context="notebook",
        rc={
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "grid.alpha": 0.25,
            "axes.edgecolor": "#D0D5DD",
            "axes.linewidth": 0.9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "legend.frameon": True,
            "legend.framealpha": 0.9,
        },
    )

    # ==========================================================
    # 1) Boxplot + Lineplot (doble eje Y, línea pastel detrás)
    # ==========================================================
    df_box = df_all.copy()
    df_box["periodo"] = pd.to_datetime(df_box["periodo"], errors="coerce").dt.strftime("%Y-%m")
    df_box["periodo"] = df_box["periodo"].astype(str)

    order_periodos = sorted(df_box["periodo"].dropna().unique().tolist())

    df_line = (
        df_box.groupby("periodo", as_index=False)["kwh"]
        .sum()
        .rename(columns={"kwh": "kwh_total"})
    )

    df_line["periodo"] = pd.Categorical(
        df_line["periodo"],
        categories=order_periodos,
        ordered=True,
    )
    df_line = df_line.sort_values("periodo")

    pos_map = {p: i for i, p in enumerate(order_periodos)}
    x_pos = df_line["periodo"].astype(str).map(pos_map).astype(float)

    fig, ax = plt.subplots(figsize=(10.4, 4.8))


    # EJE DERECHO (línea detrás)

    ax2 = ax.twinx()

    # Color pastel azul suave
    pastel_line_color = "#F4B183"

    ax2.plot(
        x_pos,
        df_line["kwh_total"].values,
        linewidth=2.2,
        color=pastel_line_color,
        alpha=0.9,
        zorder=1,  # ← detrás
        label="Total mensual",
    )

    ax2.set_ylabel("kWh total mensual")
    ax2.yaxis.set_major_formatter(FuncFormatter(_fmt_thousands))
    ax2.grid(False)

    # Hace el fondo transparente para que no tape el boxplot
    ax2.patch.set_alpha(0)

    sns.despine(ax=ax2, top=True, left=True)

 
    # BOX PLOT (encima)

    sns.boxplot(
        data=df_box,
        x="periodo",
        y="kwh",
        order=order_periodos,
        ax=ax,
        width=0.55,
        fliersize=2.2,
        linewidth=1.0,
        color="#D9ECFF",
        zorder=3,  # ← encima
    )

    for patch in ax.artists:
        patch.set_edgecolor("#1F3A5F")
        patch.set_linewidth(1.0)

    for line in ax.lines:
        line.set_color("#1F3A5F")
        line.set_linewidth(1.0)

    ax.set_title("Vertimientos por empresa en cada mes (kWh)")
    ax.set_xlabel("Periodo")
    ax.set_ylabel("kWh (distribución)")
    ax.yaxis.set_major_formatter(FuncFormatter(_fmt_thousands))
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(True, axis="y", alpha=0.25)

    sns.despine(ax=ax, top=True, right=True)

    # Leyenda (solo de la línea)
    leg = ax2.legend(
        loc="upper right",
        bbox_to_anchor=(0.99, 0.99),
        frameon=True,
        fontsize=9,
    )
    leg.get_frame().set_facecolor("white")
    leg.get_frame().set_alpha(0.9)

    fig.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.20)
    _guardar_fig(fig, os.path.join(outdir, "boxplot.svg"), dpi=dpi)

    # ==========================================================
    # 2) Gráfico CMG (múltiples series) - Seaborn lineplot
    # ==========================================================

    gdf_reg=generar_mapa_regiones(SHP_REGIONES)
    df_c = df_cmg.copy()
    df_c["fecha_version"] = pd.to_datetime(df_c["fecha_version"], errors="coerce")
    df_c = df_c.sort_values("fecha_version")
    # Renombrar valores en la columna nombre_cmg
    rename_map = {
        "CRUCERO_______220": "Barra crucero 200kV",
        "P.AZUCAR______220": "Barra Pan de Azucar 220kV",
        "QUILLOTA______220": "Barra Quillota 220kV",
        "AJAHUEL_______500": "Barra Alto Jahuel 500kV",
        "CHARRUA_______500": "Barra Charrua 500kV",
        "P.MONTT_______220": "Barra Puerto Montt 220kV"

    }
    df_c["nombre_cmg"] = df_c["nombre_cmg"].replace(rename_map)

    graficar_cmg_con_mapa(df_cmg=df_c,
                          gdf_reg=gdf_reg,
                          bar_points= BAR_POINTS,
                          out_path=os.path.join(outdir, "cmg.svg")
                          )

