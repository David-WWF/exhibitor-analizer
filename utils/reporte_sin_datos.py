import json
import os


def generar_reporte_sin_datos(ruta_json, ruta_salida_txt):
    """
    Función independiente para auditar empresas sin apollo_ids.
    Crea un archivo .txt en la ruta especificada.
    """
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error al leer el JSON: {e}")
        return

    empresas_sin_datos = []
    contador_sin_datos = 0

    # Recorremos el JSON buscando las que no tienen IDs
    for registro in data.get('results', []):
        ids = registro.get('apollo_ids', [])

        # Si la lista está vacía o no existe
        if not ids:
            nombre = registro.get('exhibitorName', "Nombre desconocido")
            empresas_sin_datos.append(nombre)
            contador_sin_datos += 1

    # 1. Imprimir contador por consola
    print("\n" + "=" * 40)
    print(f"REPORTE DE AUDITORÍA JSON")
    print("=" * 40)
    print(f"Empresas sin apollo_ids detectadas: {contador_sin_datos}")
    print("=" * 40)

    # 2. Crear archivo .txt con el listado en la carpeta DATA
    try:
        with open(ruta_salida_txt, 'w', encoding='utf-8') as f:
            f.write("LISTADO DE EMPRESAS SIN DATOS (APOLLO_IDS VACÍO)\n")
            f.write("=" * 50 + "\n")
            for nombre in empresas_sin_datos:
                f.write(f"- {nombre}\n")

        print(f"Archivo generado con éxito en: {ruta_salida_txt}")
    except Exception as e:
        print(f"Error al escribir el archivo TXT en la carpeta data: {e}")


if __name__ == "__main__":
    # --- LÓGICA DE RUTAS RELATIVAS (PyCharm Friendly) ---

    # Ruta de este archivo (ej: C:/.../Exhibitors/utils/auditoria.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Subimos un nivel a la raíz (C:/.../Exhibitors/)
    root_dir = os.path.dirname(script_dir)

    # Definimos las rutas finales
    ruta_input_json = os.path.join(root_dir, 'exhibitor_webs.json')

    # Definimos que el TXT se guarde en la carpeta 'data'
    ruta_output_txt = os.path.join(root_dir, 'data', 'listado_sindatos.txt')

    # Ejecutamos la función pasando ambas rutas
    generar_reporte_sin_datos(ruta_input_json, ruta_output_txt)