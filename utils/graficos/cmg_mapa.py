import geopandas as gpd
import pandas as pd 
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import seaborn as sns
from matplotlib.lines import Line2D
import numpy as np
from .helpers import _guardar_fig

MESES_ES = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


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


def graficar_cmg_con_mapa(
    df_cmg,
    df_cmg_comparacion,
    gdf_reg,
    bar_points,
    out_path,
    mes_reporte: int,
    anio_reporte: int,
    figsize=(7.2, 3.2),
    font_scale=1.0,
    dpi=300
):
    fs_tick  = round(8 * font_scale)
    fs_leg   = round(7 * font_scale)
    fs_leg_t = round(8 * font_scale)

    # ── Ventana estudio: enero año en curso → mes de estudio ──────
    fecha_ini_estudio = pd.Timestamp(year=anio_reporte, month=1, day=1)
    fecha_fin_estudio = (
        pd.Timestamp(year=anio_reporte, month=mes_reporte, day=1)
        + pd.offsets.MonthEnd(0)
    )

    # ── Ventana comparación: año anterior completo ────────────────
    fecha_ini_comp = pd.Timestamp(year=anio_reporte - 1, month=1,  day=1)
    fecha_fin_comp = pd.Timestamp(year=anio_reporte - 1, month=12, day=31) + pd.offsets.MonthEnd(0)

    df_c = df_cmg.copy()
    df_c["fecha_hora"] = pd.to_datetime(df_c["fecha_hora"], errors="coerce")
    df_c = df_c.dropna(subset=["fecha_hora", "CMG_DOLAR_MWH", "nombre_cmg"])
    df_c = df_c[
        (df_c["fecha_hora"] >= fecha_ini_estudio) &
        (df_c["fecha_hora"] <= fecha_fin_estudio)
    ].copy()

    df_comp = df_cmg_comparacion.copy()
    df_comp["fecha_hora"] = pd.to_datetime(df_comp["fecha_hora"], errors="coerce")
    df_comp = df_comp.dropna(subset=["fecha_hora", "CMG_DOLAR_MWH", "nombre_cmg"])
    df_comp = df_comp[
        (df_comp["fecha_hora"] >= fecha_ini_comp) &
        (df_comp["fecha_hora"] <= fecha_fin_comp)
    ].copy()

    if df_c.empty and df_comp.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "Sin datos para gráfico CMG", ha="center", va="center", fontsize=fs_tick)
        ax.axis("off")
        _guardar_fig(fig, out_path, dpi=dpi)
        return

    anio_estudio_label     = str(anio_reporte)
    anio_comparacion_label = str(anio_reporte - 1)

    # ── Agregar por mes con clave ordenable ───────────────────────
    for df_ in [df_c, df_comp]:
        df_["mes_num"]     = df_["fecha_hora"].dt.month
        df_["anio"]        = df_["fecha_hora"].dt.year
        df_["periodo_key"] = df_["anio"] * 100 + df_["mes_num"]

    if not df_c.empty:
        df_c = (
            df_c.groupby(["periodo_key", "mes_num", "anio", "nombre_cmg"], as_index=False)["CMG_DOLAR_MWH"]
            .mean()
            .sort_values(["nombre_cmg", "periodo_key"])
        )

    if not df_comp.empty:
        df_comp = (
            df_comp.groupby(["periodo_key", "mes_num", "anio", "nombre_cmg"], as_index=False)["CMG_DOLAR_MWH"]
            .mean()
            .sort_values(["nombre_cmg", "periodo_key"])
        )

    barras = sorted(
        set(df_c["nombre_cmg"].dropna().unique()).union(
            set(df_comp["nombre_cmg"].dropna().unique())
        )
    )

    # ── Paletas diferenciadas: muted para estudio, pastel para comparación ──
    palette_estudio     = sns.color_palette("pastel",  n_colors=len(barras))
    palette_comparacion = sns.color_palette("pastel", n_colors=len(barras))
    color_map_estudio   = dict(zip(barras, palette_estudio))
    color_map_comp      = dict(zip(barras, palette_comparacion))

    # ── Eje X: comparación shifteada + estudio ────────────────────
    periodos_comp_shifted = set()
    if not df_comp.empty:
        periodos_comp_shifted = set(
            ((df_comp["anio"] + 1) * 100 + df_comp["mes_num"]).unique()
        )
    periodos_estudio   = set(df_c["periodo_key"].unique()) if not df_c.empty else set()
    periodos_ordenados = sorted(periodos_comp_shifted | periodos_estudio)
    n_meses            = len(periodos_ordenados)
    x                  = np.arange(n_meses)
    periodo_to_x       = {pk: i for i, pk in enumerate(periodos_ordenados)}

    def _label(pk):
        mes = pk % 100
        return MESES_ES[mes]   # ← solo mes, sin año

    xtick_labels = [_label(pk) for pk in periodos_ordenados]

    # ── Figura ────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=figsize)
    ax_map  = fig.add_axes([1, 0.25, 0.20, 0.63])
    ax_map.grid(False)

    # ── Barras año en curso — paleta muted, alpha pleno ──────────
    ancho_barra = 0.8 / len(barras)
    offsets     = np.linspace(
        -(len(barras) - 1) / 2,
         (len(barras) - 1) / 2,
        len(barras)
    ) * ancho_barra

    for i, barra in enumerate(barras):
        g = df_c[df_c["nombre_cmg"] == barra].copy()
        if g.empty:
            continue
        xs = [periodo_to_x[pk] for pk in g["periodo_key"] if pk in periodo_to_x]
        ys = [g.loc[g["periodo_key"] == pk, "CMG_DOLAR_MWH"].iloc[0]
              for pk in g["periodo_key"] if pk in periodo_to_x]
        ax.bar(
            np.array(xs) + offsets[i], ys,
            width=ancho_barra, color=color_map_estudio[barra],
            alpha=0.90, linewidth=0, zorder=3
        )

    # ── Línea comparación — pastel, borde blanco, encima de barras ──
    for barra in barras:
        g = df_comp[df_comp["nombre_cmg"] == barra].copy()
        if g.empty:
            continue
        g["periodo_key_shifted"] = (g["anio"] + 1) * 100 + g["mes_num"]
        pairs = [
            (periodo_to_x[row["periodo_key_shifted"]], row["CMG_DOLAR_MWH"])
            for _, row in g.iterrows()
            if row["periodo_key_shifted"] in periodo_to_x
        ]
        if pairs:
            xs_, ys_ = zip(*pairs)
            xs_sorted, ys_sorted = zip(*sorted(zip(xs_, ys_)))
            ax.plot(
                xs_sorted, ys_sorted,
                linestyle="-", linewidth=2.0,
                color=color_map_comp[barra],
                alpha=0.9, zorder=5,
            )

    # ── Ejes ──────────────────────────────────────────────────────
    ax.set_xticks(x)
    ax.set_xticklabels(xtick_labels, fontsize=fs_tick)
    ax.set_xlim(-0.5, n_meses - 0.5)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=fs_tick)
    ax.grid(False)
    ax.yaxis.grid(True, alpha=0.18, linewidth=0.8)
    ax.xaxis.grid(False)
    sns.despine(ax=ax)

    # ── Mapa ──────────────────────────────────────────────────────
    gdf_reg.sort_values("CUT_REG").reset_index(drop=True).plot(
        ax=ax_map, color="#B0B0B0", edgecolor="white", linewidth=0.6, zorder=1
    )
    rows = [
        {"nombre_cmg": b, "lon": bar_points[b]["lon"], "lat": bar_points[b]["lat"]}
        for b in barras if b in bar_points
    ]
    if rows:
        pts = gpd.GeoDataFrame(
            rows,
            geometry=gpd.points_from_xy([r["lon"] for r in rows], [r["lat"] for r in rows]),
            crs="EPSG:4326"
        ).to_crs(gdf_reg.crs)
        for _, r in pts.iterrows():
            ax_map.scatter(
                r.geometry.x, r.geometry.y, s=28, marker="o",
                color=color_map_estudio[r["nombre_cmg"]],
                edgecolor="white", linewidth=0.6, zorder=5
            )

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

    # ── Leyendas ──────────────────────────────────────────────────
    handles_barras = [
        Line2D([0], [0], color=color_map_estudio[b], linewidth=0,
               marker="s", markersize=7,
               markerfacecolor=color_map_estudio[b], markeredgecolor="white",
               label=b)
        for b in barras
    ]
    leg1 = ax.legend(
        handles=handles_barras, title="Barras CMG",
        loc="lower left", fontsize=fs_leg, title_fontsize=fs_leg_t,
        frameon=True, ncol=2, bbox_to_anchor=(0.0, -0.51), borderaxespad=0
    )
    leg1.get_frame().set_alpha(0.9)
    ax.add_artist(leg1)

    handles_estilo = [
        Line2D([0], [0], color="#667085", linewidth=0,
               marker="s", markersize=7,
               label=f"{anio_estudio_label} (barras)"),
        Line2D([0], [0], color="#667085", linewidth=2.0,
               linestyle="-", label=f"{anio_comparacion_label} (referencia)"),
    ]
    leg2 = ax.legend(
        handles=handles_estilo, title="Período",
        loc="lower left", fontsize=fs_leg, title_fontsize=fs_leg_t,
        frameon=True, ncol=1, bbox_to_anchor=(0.4, -0.537), borderaxespad=0.6
    )
    leg2.get_frame().set_alpha(0.9)

    fig.subplots_adjust(left=0.08, right=0.98, top=0.84, bottom=0.4)
    _guardar_fig(fig, out_path, dpi=dpi)