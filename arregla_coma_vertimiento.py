import pandas as pd
import csv

BASE = r"C:\Users\Pablo\OneDrive\Documents\Trabajo\proyectos\reporte_generacion\data\raw\db"
ruta = BASE + r"\gx_real_trim.csv"

# Ver líneas crudas
print("=== LÍNEAS CRUDAS ===")
with open(ruta, encoding="utf-8") as f:
    for i, line in enumerate(f):
        print(f"línea {i}: {repr(line)}")
        if i >= 2:
            break

# Ver cómo lo lee pandas con quoting=3
print("\n=== PANDAS quoting=3 ===")
df = pd.read_csv(ruta, sep=";", dtype=str, quoting=3)
print("shape:", df.shape)
print("columnas:", df.columns.tolist())
print(df.iloc[0])