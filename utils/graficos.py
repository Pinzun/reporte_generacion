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

def graficar_cmg_con_mapa(df_cmg, gdf_reg, bar_points, out_path, dpi=130):
    df_c = df_cmg.copy()
    df_c["fecha_hora"] = pd.to_datetime(df_c["fecha_hora"], errors="coerce")
    df_c = df_c.dropna(subset=["fecha_hora", "CMG_PESO_KWH", "nombre_cmg"]).copy()
    df_c = df_c.sort_values("fecha_hora")

    # Tamaño compacto pensado para card horizontal
    fig, ax = plt.subplots(figsize=(7.2, 3.2))

    # Inset del mapa más pequeño y menos invasivo
    ax_map = fig.add_axes([0.9, 0.34, 0.16, 0.6])
    ax_map.grid(False)

    # -------------------------
    # Paleta fija por barra
    # -------------------------
    barras = sorted(df_c["nombre_cmg"].dropna().unique())
    palette = sns.color_palette("pastel", n_colors=len(barras))
    color_map = dict(zip(barras, palette))

    # -------------------------
    # Lineplot
    # -------------------------
    sns.lineplot(
        data=df_c,
        x="fecha_hora",
        y="CMG_PESO_KWH",
        hue="nombre_cmg",
        hue_order=barras,
        palette=color_map,
        ax=ax,
        linewidth=1.8,
        estimator=None,
        legend=False,
    )

    ax.set_title("Costo marginal promedio por mes ($/kWh)", fontsize=11, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("CMG ($/kWh)", fontsize=9)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(False)
    ax.yaxis.grid(True, alpha=0.18, linewidth=0.8)
    ax.xaxis.grid(False)
    sns.despine(ax=ax)

    # -------------------------
    # Mapa fondo
    # -------------------------
    gdf_reg_plot = gdf_reg.sort_values("CUT_REG").reset_index(drop=True)

    PASTEL_ORANGE = "#F6B38E"
    PASTEL_BLUE = "#8EC5FF"

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
        linewidth=0.6,
        zorder=1
    )

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
                s=28,
                marker="o",
                color=color_map[b],
                edgecolor="white",
                linewidth=0.6,
                zorder=5
            )

    minx, miny, maxx, maxy = gdf_reg.total_bounds
    dx, dy = maxx - minx, maxy - miny
    ax_map.set_xlim(minx - 0.08 * dx, maxx + 0.08 * dx)
    ax_map.set_ylim(miny - 0.03 * dy, maxy + 0.03 * dy)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")
    ax_map.set_facecolor(ax.get_facecolor())
    ax_map.patch.set_alpha(1.0)

    for spine in ax_map.spines.values():
        spine.set_visible(True)
        spine.set_color("#D0D5DD")
        spine.set_linewidth(0.7)

    # -------------------------
    # Leyenda compacta abajo-izquierda
    # -------------------------
    handles = [
        Line2D(
            [0], [0],
            color=color_map[b],
            linewidth=1.8,
            marker="o",
            markersize=4.5,
            markerfacecolor=color_map[b],
            markeredgecolor="white",
            label=b
        )
        for b in barras
    ]

    leg = ax.legend(
        handles=handles,
        title="Barras CMG",
        loc="lower left",
        fontsize=7,
        title_fontsize=8,
        frameon=True,
        ncol=2,
        borderaxespad=0.6
    )
    leg.get_frame().set_alpha(0.9)

    fig.subplots_adjust(left=0.08, right=0.98, top=0.84, bottom=0.24)

    _guardar_fig(fig, out_path, dpi=dpi)

def graficar_gx_tipico(df_dia_tipico, out_path, dpi=130):
    """
    Grafica el día típico real como áreas apiladas por tecnología.
    Mantiene separados los BESS en inyección y retiro para evitar neteo.
    """
    df = df_dia_tipico.copy()

    if df.empty:
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        ax.text(0.5, 0.5, "Sin datos para día típico", ha="center", va="center", fontsize=11)
        ax.axis("off")
        _guardar_fig(fig, out_path, dpi=dpi)
        return

    df["inyeccion_retiro"] = pd.to_numeric(df["inyeccion_retiro"], errors="coerce")
    df = df.dropna(subset=["inyeccion_retiro", "tipo"]).copy()

    # Asegurar ejes temporales
    if "hora_decimal" not in df.columns:
        if {"hora", "minuto"}.issubset(df.columns):
            df["hora"] = pd.to_numeric(df["hora"], errors="coerce").fillna(0)
            df["minuto"] = pd.to_numeric(df["minuto"], errors="coerce").fillna(0)
            df["hora_decimal"] = df["hora"] + df["minuto"] / 60.0
        else:
            df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
            df["hora_decimal"] = df["fecha_hora"].dt.hour + df["fecha_hora"].dt.minute / 60.0

    df["tipo"] = df["tipo"].fillna("Sin clasificar").astype(str).str.strip()
    df["subtipo"] = df["subtipo"].fillna("-").astype(str).str.strip()

    rename_tipo = {
        "Eólicas": "Eólica",
        "Solar": "Solar",
        "Solares": "Solar",
        "Hidroeléctrica": "Hidro",
        "Hidroeléctricas": "Hidro",
        "Hidro": "Hidro",
        "Térmica": "Térmica",
        "Térmicas": "Térmica",
        "Termica": "Térmica",
        "Termicas": "Térmica",
        "Geotérmica": "Geotérmica",
        "Geotermia": "Geotérmica",
        "Bess": "BESS",
        "BESS": "BESS",
    }
    df["tipo_plot"] = df["tipo"].replace(rename_tipo)

    # Separar BESS inyección y retiro
    df["categoria_plot"] = df["tipo_plot"]

    mask_bess = df["tipo_plot"].eq("BESS")
    mask_retiro = df["subtipo"].str.contains("Retiro", case=False, na=False)
    mask_iny = df["subtipo"].str.contains("Inye", case=False, na=False)

    df.loc[mask_bess & mask_retiro, "categoria_plot"] = "BESS Retiro"
    df.loc[mask_bess & mask_iny, "categoria_plot"] = "BESS Inyección"

    df_plot = (
        df.groupby(["hora_decimal", "categoria_plot"], as_index=False)["inyeccion_retiro"]
        .sum()
    )

    print("Horas únicas df_dia_tipico:", sorted(df["hora_decimal"].dropna().unique())[:30])
    print("Cantidad de horas únicas df_dia_tipico:", df["hora_decimal"].nunique())

    if df_plot.empty:
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        ax.text(0.5, 0.5, "Sin datos para graficar el día típico", ha="center", va="center", fontsize=11)
        ax.axis("off")
        _guardar_fig(fig, out_path, dpi=dpi)
        return

    pivot = (
        df_plot.pivot(index="hora_decimal", columns="categoria_plot", values="inyeccion_retiro")
        .fillna(0)
        .sort_index()
    )

    print("Horas únicas gx_tipico:", pivot.index.tolist()[:30])
    print("Cantidad horas únicas gx_tipico:", len(pivot.index))
    print("Suma total pivot:", pivot.to_numpy().sum())

    if pivot.empty or len(pivot.index) <= 1 or np.isclose(pivot.to_numpy().sum(), 0):
        fig, ax = plt.subplots(figsize=(7.2, 3.2))
        ax.text(
            0.5, 0.5,
            "No hay resolución horaria suficiente para construir el gráfico",
            ha="center", va="center", fontsize=11
        )
        ax.axis("off")
        _guardar_fig(fig, out_path, dpi=dpi)
        return

    orden_tipos = [
        "Solar",
        "Eólica",
        "Hidro",
        "Geotérmica",
        "Térmica",
        "BESS Inyección",
        "BESS Retiro",
    ]
    tipos_presentes = [t for t in orden_tipos if t in pivot.columns]
    tipos_restantes = sorted([t for t in pivot.columns if t not in tipos_presentes])
    cols = tipos_presentes + tipos_restantes
    pivot = pivot[cols]

    color_map = {
        "Solar": "#F6C48E",
        "Eólica": "#A8D5BA",
        "Hidro": "#8EC5FF",
        "Geotérmica": "#D9C2A3",
        "Térmica": "#C9C2E6",
        "BESS Inyección": "#D96C6C",
        "BESS Retiro": "#6FA8DC",
    }

    fig, ax = plt.subplots(figsize=(10, 5))

    x = pivot.index.values

    cols_pos = [c for c in pivot.columns if pivot[c].max() > 0]
    cols_neg = [c for c in pivot.columns if pivot[c].min() < 0]

    if cols_pos:
        ax.stackplot(
            x,
            [pivot[c].clip(lower=0).values for c in cols_pos],
            labels=cols_pos,
            colors=[color_map.get(c, "#D9E2EC") for c in cols_pos],
            alpha=0.95,
            linewidth=0.6,
        )

    if cols_neg:
        ax.stackplot(
            x,
            [pivot[c].clip(upper=0).values for c in cols_neg],
            labels=cols_neg,
            colors=[color_map.get(c, "#D9E2EC") for c in cols_neg],
            alpha=0.95,
            linewidth=0.6,
        )

    ax.axhline(0, color="#667085", linewidth=0.8)

    ax.set_title("Generación diaria típica por tecnología", fontsize=11, fontweight="bold")
    ax.set_xlabel("Hora del día", fontsize=9)
    ax.set_ylabel("Generación", fontsize=9)
    ax.yaxis.set_major_formatter(FuncFormatter(_fmt_thousands))
    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)
    ax.grid(True, axis="y", alpha=0.18)
    ax.grid(False, axis="x")

    xticks = np.arange(0, 25, 4)
    ax.set_xticks(xticks)
    ax.set_xlim(0, 24)
    ax.set_xticklabels([f"{int(h):02d}:00" for h in xticks])

    sns.despine(ax=ax, top=True, right=True)

    leg = ax.legend(
        title="Tecnología",
        loc="upper right",
        fontsize=7,
        title_fontsize=8,
        frameon=True,
        ncol=2
    )
    leg.get_frame().set_alpha(0.9)

    fig.subplots_adjust(left=0.08, right=0.98, top=0.84, bottom=0.20)

    _guardar_fig(fig, out_path, dpi=dpi)

    
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import seaborn as sns


def graficar_spread_cmg(df_spread: pd.DataFrame, out_path: str, dpi: int = 130):
    """
    Grafica barras agrupadas por nombre_cmg:
    - una barra para horas_solares
    - una barra para horas_no_solares
    """
    columnas_requeridas = {"nombre_cmg", "horas_solares", "horas_no_solares"}
    faltantes = columnas_requeridas - set(df_spread.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en df_spread: {sorted(faltantes)}")

    df_plot = df_spread.copy()

    # Ordenar por spread absoluto, de mayor a menor, para que se lea mejor
    if "spread_abs" in df_plot.columns:
        df_plot = df_plot.sort_values("spread_abs", ascending=False).reset_index(drop=True)

    x = np.arange(len(df_plot))
    width = 0.38

    fig, ax = plt.subplots(figsize=(8.2, 4.2))

    color_solar = "#F6C48E"      # naranjo pastel
    color_no_solar = "#8EC5FF"   # azul pastel

    ax.bar(
        x - width / 2,
        df_plot["horas_solares"],
        width=width,
        label="Horas solares",
        color=color_solar,
        edgecolor="white",
        linewidth=0.8,
    )

    ax.bar(
        x + width / 2,
        df_plot["horas_no_solares"],
        width=width,
        label="Horas no solares",
        color=color_no_solar,
        edgecolor="white",
        linewidth=0.8,
    )

    ax.set_title("CMG promedio: horas solares vs no solares", fontsize=12, fontweight="bold")
    ax.set_xlabel("Barra CMG", fontsize=10)
    ax.set_ylabel("CMG promedio ($/kWh)", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(df_plot["nombre_cmg"], rotation=35, ha="right", fontsize=8)
    ax.tick_params(axis="y", labelsize=8)

    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:,.0f}".replace(",", ".")))

    ax.grid(True, axis="y", alpha=0.18)
    ax.grid(False, axis="x")
    sns.despine(ax=ax, top=True, right=True)

    leg = ax.legend(frameon=True, fontsize=8)
    leg.get_frame().set_alpha(0.9)

    fig.subplots_adjust(left=0.09, right=0.98, top=0.87, bottom=0.28)

    _guardar_fig(fig, out_path, dpi=dpi)

def graficar_boxplot_vertimientos_con_total(df_all, out_path, dpi=130):
    """
    Genera un gráfico combinado:
    - boxplot de vertimientos por empresa en cada mes (eje izquierdo)
    - línea de vertimiento total mensual (eje derecho)

    Requiere columnas:
    - periodo
    - vertimiento
    """

    columnas_requeridas = {"periodo", "vertimiento"}
    faltantes = columnas_requeridas - set(df_all.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {sorted(faltantes)}")

    df_box = df_all.copy()

    df_box["periodo"] = pd.to_datetime(df_box["periodo"], errors="coerce").dt.strftime("%Y-%m")
    df_box["periodo"] = df_box["periodo"].astype(str)

    df_box["vertimiento"] = pd.to_numeric(df_box["vertimiento"], errors="coerce")
    df_box = df_box.dropna(subset=["periodo", "vertimiento"]).copy()

    if df_box.empty:
        fig, ax = plt.subplots(figsize=(10.4, 4.8))
        ax.text(0.5, 0.5, "Sin datos para graficar", ha="center", va="center", fontsize=12)
        ax.axis("off")
        _guardar_fig(fig, out_path, dpi=dpi)
        return

    order_periodos = sorted(df_box["periodo"].dropna().unique().tolist())

    # =========================
    # Totales mensuales
    # =========================
    df_line = (
        df_box.groupby("periodo", as_index=False)["vertimiento"]
        .sum()
        .rename(columns={"vertimiento": "kwh_total"})
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

    # ==================================================
    # EJE DERECHO (línea de total mensual)
    # ==================================================
    ax2 = ax.twinx()

    pastel_line_color = "#F4B183"

    ax2.plot(
        x_pos,
        df_line["kwh_total"].values,
        linewidth=2.2,
        color=pastel_line_color,
        alpha=0.9,
        zorder=1,
        label="Total mensual",
    )

    ax2.set_ylabel("kWh total mensual")
    ax2.yaxis.set_major_formatter(FuncFormatter(_fmt_thousands))
    ax2.grid(False)

    ax2.patch.set_alpha(0)

    sns.despine(ax=ax2, top=True, left=True)

    # ==================================================
    # BOX PLOT (distribución)
    # ==================================================
    sns.boxplot(
        data=df_box,
        x="periodo",
        y="vertimiento",
        order=order_periodos,
        ax=ax,
        width=0.55,
        fliersize=2.2,
        linewidth=1.0,
        color="#D9ECFF",
        zorder=3,
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

    # Leyenda
    leg = ax2.legend(
        loc="upper right",
        bbox_to_anchor=(0.99, 0.99),
        frameon=True,
        fontsize=9,
    )
    leg.get_frame().set_facecolor("white")
    leg.get_frame().set_alpha(0.9)

    fig.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.20)

    _guardar_fig(fig, out_path, dpi=dpi)

def generar_graficas(
    df_all,
    df_spread,
    df_cmg,
    df_dia_tipico,
    outdir="outputs",
    dpi=130,
            ):

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
    # 1) Boxplot + línea de total mensual
    # ==========================================================
    graficar_boxplot_vertimientos_con_total(
        df_all=df_all,
        out_path=os.path.join(outdir, "boxplot.svg"),
        dpi=dpi,
    )

    # ==========================================================
    # 2) Gráfico CMG (múltiples series) - Seaborn lineplot
    # ==========================================================

    gdf_reg=generar_mapa_regiones(SHP_REGIONES)
    df_c = df_cmg.copy()
    df_c["fecha_hora"] = pd.to_datetime(df_c["fecha_hora"], errors="coerce")
    df_c = df_c.sort_values("fecha_hora")
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
    
    # ==========================================================
    # 3) Generación típica diaria (área apilada)
    # ==========================================================
    graficar_gx_tipico(
        df_dia_tipico=df_dia_tipico,
        out_path=os.path.join(outdir, "gx_tipico.svg"),
        dpi=dpi
    )

    # ==========================================================
    # 4) Spread CMG
    # ========================================================== 

    graficar_spread_cmg(
        df_spread=df_spread,
        out_path=os.path.join(outdir, "spread_cmg.svg"),
        dpi=dpi
    )


