import json
import os


def filter_exhibitors(input_path: str, output_path: str):

    ALLOWED_SECTORS = {
        "GROCERY PRODUCTS",
        "LANDS OF SPAIN",
        "RESTAURAMA",
        "SNACKS, BISCUITS & CONFECTIONERY",
        "THE ALIMENTARIA TRENDS"
    }

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No se encuentra el archivo: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Identificamos dónde están las filas (rows o results)
    key_name = "rows" if "rows" in data else "results"
    original_rows = data.get(key_name, [])
    original_count = len(original_rows)

    # Solo si el sector está en nuestra lista blanca
    filtered_rows = [
        row for row in original_rows
        if str(row.get("sectorName", "")).strip().upper() in ALLOWED_SECTORS
    ]

    new_count = len(filtered_rows)
    removed_count = original_count - new_count

    # Actualizamos el objeto data
    data[key_name] = filtered_rows
    data["count_total"] = new_count

    # Guardamos el resultado
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"🎯 Filtrado (Solo sectores objetivo) completado:")
    print(f"   - Total procesados: {original_count}")
    print(f"   - Empresas descartadas: {removed_count}")
    print(f"   - Empresas mantenidas: {new_count}")


if __name__ == "__main__":
    # Prueba manual si ejecutas el archivo directamente
    filter_exhibitors("exhibitors_enriched.json", "exhibitors_filtered.json")