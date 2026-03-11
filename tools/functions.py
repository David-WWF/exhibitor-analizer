from typing import Dict, Any

import pandas as pd
from fastapi import HTTPException

#TODO Revisar version instalación

def read_csv(ruta_csv):
    try:
        df = pd.read_csv(ruta_csv)

        #print(df.head())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archico no encontrado.")

#Obtiene una lista de nombres de empresas
def obtener_nombres_db(ruta_csv):
    try:
        df = pd.read_csv(ruta_csv)
        # .dropna() elimina valores nulos si los hubiera
        # .tolist() convierte la columna de Pandas a una lista nativa de Python
        return df['exhibitorName'].dropna().tolist()
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return []

#Obtiene el body de una empresa
def exhibitor_por_nombre(ruta_csv, exhibitor):
    try:
        #print(f"{exhibitor.exhibitorName}")
        df = pd.read_csv(ruta_csv)

        # Si no viene nombre en el request
        if not exhibitor.exhibitorName:
            return {"error": "exhibitorName es requerido"}

        # Búsqueda parcial (no sensible a mayúsculas/minúsculas)
        resultado = df[df["exhibitorName"].str.contains(
            exhibitor.exhibitorName,
            case=False,
            na=False
        )]

        if resultado.empty:
            return {"message": "No se encontró la empresa"}

        return {
            "status": "success",
            "count": len(resultado),
            "data": resultado.to_dict(orient="records")
        }

    except Exception as e:
        return {"error": str(e)}

def clean_csv_without_description(
    csv_path: str,
    out_csv_path: str = "exhibitors_cleaned.csv",
    description_column: str = "description_es",
    verbose: bool = True
) -> Dict[str, Any]:

    try:
        df = pd.read_csv(csv_path)

        if description_column not in df.columns:
            raise ValueError(
                f"No existe la columna '{description_column}' en el CSV. "
                f"Columnas disponibles: {list(df.columns)}"
            )

        total_before = len(df)

        # Eliminar NaN
        df_cleaned = df[df[description_column].notna()]

        # Eliminar vacíos o solo espacios
        df_cleaned = df_cleaned[
            df_cleaned[description_column].astype(str).str.strip() != ""
        ]

        total_after = len(df_cleaned)
        removed = total_before - total_after

        # Guardar CSV limpio
        df_cleaned.to_csv(out_csv_path, index=False)

        if verbose:
            print("\n[CLEAN CSV]")
            print(f"Total antes: {total_before}")
            print(f"Total después: {total_after}")
            print(f"Eliminados: {removed}")
            print(f"Archivo guardado en: {out_csv_path}")

        return {
            "status": "success",
            "total_before": total_before,
            "total_after": total_after,
            "removed": removed,
            "out_csv_path": out_csv_path
        }

    except Exception as e:
        print(f"[ERROR CLEAN CSV] {e}")
        return {"status": "error", "message": str(e)}