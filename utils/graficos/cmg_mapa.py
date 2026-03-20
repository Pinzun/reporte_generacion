#IMPORTACION DE LIBRERIAS GENERALES
import geopandas as gpd
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
#IMPORTACION DE HELPERS
from .helpers import _guardar_fig

# ══════════════════════════════════════════════════════════════════════════════
# MAPA DE REGIONES
# ══════════════════════════════════════════════════════════════════════════════

def generar_mapa_regiones(shp_path, target_crs="EPSG:32719"):
    CUT_COM_EXCLUIR  = [5201, 5104]
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
    return gdf.sort_values("CUT_REG").reset_index(drop=True)



# ══════════════════════════════════════════════════════════════════════════════
# CMG CON MAPA
# ══════════════════════════════════════════════════════════════════════════════

def graficar_cmg_con_mapa(
    df_cmg,
    df_cmg_comparacion,
    gdf_reg,
    bar_points,
    out_path,
    figsize=(7.2, 3.2),
    font_scale=1.0,
    dpi=300
):
    import calendar

    # ── Tamaños de fuente escalados ───────────────────────────────
    fs_title  = round(11 * font_scale)
    fs_label  = round(9  * font_scale)
    fs_tick   = round(8  * font_scale)
    fs_leg    = round(7  * font_scale)
    fs_leg_t  = round(8  * font_scale)

    df_c = df_cmg.copy()
    df_c["fecha_hora"] = pd.to_datetime(df_c["fecha_hora"], errors="coerce")
    df_c = df_c.dropna(subset=["fecha_hora", "CMG_PESO_KWH", "nombre_cmg"]).copy()

    df_comp = df_cmg_comparacion.copy()
    df_comp["fecha_hora"] = pd.to_datetime(df_comp["fecha_hora"], errors="coerce")
    df_comp = df_comp.dropna(subset=["fecha_hora", "CMG_PESO_KWH", "nombre_cmg"]).copy()

    if df_c.empty and df_comp.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "Sin datos para gráfico CMG", ha="center", va="center", fontsize=fs_title)
        ax.axis("off")
        _guardar_fig(fig, out_path, dpi=dpi)
        return

    anio_estudio     = str(df_c["fecha_hora"].dt.year.mode().iloc[0])    if not df_c.empty    else "Año estudio"
    anio_comparacion = str(df_comp["fecha_hora"].dt.year.mode().iloc[0]) if not df_comp.empty else "Año anterior"

    for df_ in [df_c, df_comp]:
        if not df_.empty:
            df_["mes_num"] = df_["fecha_hora"].dt.month

    if not df_c.empty:
        df_c = (
            df_c.groupby(["mes_num", "nombre_cmg"], as_index=False)["CMG_PESO_KWH"]
            .mean()
            .sort_values(["nombre_cmg", "mes_num"])
        )

    if not df_comp.empty:
        df_comp = (
            df_comp.groupby(["mes_num", "nombre_cmg"], as_index=False)["CMG_PESO_KWH"]
            .mean()
            .sort_values(["nombre_cmg", "mes_num"])
        )

    barras  = sorted(
        set(df_c["nombre_cmg"].dropna().unique()).union(
            set(df_comp["nombre_cmg"].dropna().unique())
        )
    )
    palette   = sns.color_palette("pastel", n_colors=len(barras))
    color_map = dict(zip(barras, palette))

    fig, ax = plt.subplots(figsize=figsize)

    ax_map = fig.add_axes([1.03, 0.2, 0.16, 0.6])
    ax_map.grid(False)

    for barra in barras:
        g = df_c[df_c["nombre_cmg"] == barra].copy()
        if g.empty:
            continue
        ax.plot(g["mes_num"], g["CMG_PESO_KWH"],
                linestyle="-", linewidth=1.8, color=color_map[barra], alpha=0.95, zorder=3)

    for barra in barras:
        g = df_comp[df_comp["nombre_cmg"] == barra].copy()
        if g.empty:
            continue
        ax.plot(g["mes_num"], g["CMG_PESO_KWH"],
                linestyle="--", linewidth=1.5, color=color_map[barra], alpha=0.95, zorder=2)

    meses = np.arange(1, 13)
    ax.set_xticks(meses)
    ax.set_xticklabels([calendar.month_abbr[m] for m in meses], fontsize=fs_tick)
    ax.set_xlim(1, 12)
    ax.set_title("Costo marginal promedio por mes ($/kWh)", fontsize=fs_title, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("CMG ($/kWh)", fontsize=fs_label)
    ax.tick_params(axis="y", labelsize=fs_tick)
    ax.grid(False)
    ax.yaxis.grid(True, alpha=0.18, linewidth=0.8)
    ax.xaxis.grid(False)
    sns.despine(ax=ax)

    gdf_reg_plot = gdf_reg.sort_values("CUT_REG").reset_index(drop=True)
    cmap = LinearSegmentedColormap.from_list("pastel_orange_blue", ["#F6B38E", "#8EC5FF"])
    colors = [cmap(i) for i in np.linspace(0, 1, len(gdf_reg_plot))]
    gdf_reg_plot["_color"] = colors
    gdf_reg_plot.plot(ax=ax_map, color=gdf_reg_plot["_color"],
                      edgecolor="white", linewidth=0.6, zorder=1)

    rows = [{"nombre_cmg": b, "lon": bar_points[b]["lon"], "lat": bar_points[b]["lat"]}
            for b in barras if b in bar_points]
    if rows:
        pts = gpd.GeoDataFrame(
            rows,
            geometry=gpd.points_from_xy([r["lon"] for r in rows], [r["lat"] for r in rows]),
            crs="EPSG:4326"
        ).to_crs(gdf_reg.crs)
        for _, r in pts.iterrows():
            ax_map.scatter(r.geometry.x, r.geometry.y, s=28, marker="o",
                           color=color_map[r["nombre_cmg"]], edgecolor="white",
                           linewidth=0.6, zorder=5)

    minx, miny, maxx, maxy = gdf_reg.total_bounds
    dx, dy = maxx - minx, maxy - miny
    ax_map.set_xlim(minx - 0.08*dx, maxx + 0.08*dx)
    ax_map.set_ylim(miny - 0.03*dy, maxy + 0.03*dy)
    ax_map.set_axis_off()
    ax_map.set_aspect("equal")
    ax_map.set_facecolor(ax.get_facecolor())
    ax_map.patch.set_alpha(1.0)
    for spine in ax_map.spines.values():
        spine.set_visible(True)
        spine.set_color("#D0D5DD")
        spine.set_linewidth(0.7)

    handles_barras = [
        Line2D([0], [0], color=color_map[b], linewidth=1.8, marker="o",
               markersize=4.5, markerfacecolor=color_map[b], markeredgecolor="white", label=b)
        for b in barras
    ]
    leg1 = ax.legend(handles=handles_barras, title="Barras CMG", loc="lower left",
                     fontsize=fs_leg, title_fontsize=fs_leg_t, frameon=True, ncol=2, borderaxespad=0.6)
    leg1.get_frame().set_alpha(0.9)
    ax.add_artist(leg1)

    handles_estilo = [
        Line2D([0], [0], color="#667085", linewidth=1.8, linestyle="-",  label=anio_estudio),
        Line2D([0], [0], color="#667085", linewidth=1.5, linestyle="--", label=anio_comparacion),
    ]
    leg2 = ax.legend(handles=handles_estilo, title="Período", loc="upper left",
                     fontsize=fs_leg, title_fontsize=fs_leg_t, frameon=True, ncol=1, borderaxespad=0.6)
    leg2.get_frame().set_alpha(0.9)

    fig.subplots_adjust(left=0.08, right=0.98, top=0.84, bottom=0.24)
    _guardar_fig(fig, out_path, dpi=dpi)