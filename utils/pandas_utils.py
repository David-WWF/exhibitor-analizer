import pandas as pd
import json
import os

def excel_enrich(ruta_excel, ruta_json):
    """
        Función para generar un listado de empresas con sus datos y añadirlo
        a un excel existente
    """

    # 1. Cargar el Excel original
    try:
        df_original = pd.read_excel(ruta_excel)
        # Normalizamos nombres de columnas: Mayúsculas y sin espacios
        df_original.columns = df_original.columns.str.upper().str.strip()
        # Creamos un set de empresas para no duplicar las que ya tienes
        empresas_existentes = set(df_original['EMPRESA'].astype(str).str.upper().str.strip())
        print(f"-> Excel cargado: {len(df_original)} empresas actuales.")
    except Exception as e:
        print(f"Error al leer el Excel: {e}")
        return

    # 2. Cargar el JSON
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error al leer el JSON: {e}")
        return

    nuevos_registros = []
    contador_ignoradas_por_existir = 0
    contador_sin_datos_contacto = 0

    # 3. Procesar y Filtrar
    for registro in data.get('results', []):
        empresa_nombre = registro.get('exhibitorName')

        # Saltamos si la empresa ya está en tu Excel
        if empresa_nombre and str(empresa_nombre).upper().strip() in empresas_existentes:
            contador_ignoradas_por_existir += 1
            continue

        web = registro.get('web_empresa')
        contactos = registro.get('contacts_info', [])

        for persona in contactos:
            email = persona.get('email')
            linkedin = persona.get('linkedin')

            # REQUISITO NUEVO: Solo incluir si tiene Mail O LinkedIn
            # Comprobamos que no sea None y que no sea una cadena vacía
            if (email and str(email).strip()) or (linkedin and str(linkedin).strip()):
                nuevos_registros.append({
                    'EMPRESA': empresa_nombre,
                    'WEB': web,
                    'NOMBRE': persona.get('name'),
                    'MAIL': email,
                    'CARGO': persona.get('title'),
                    'LINKEDIN': linkedin,
                    'MAIL ENVIADO': ''
                })
            else:
                contador_sin_datos_contacto += 1

    if not nuevos_registros:
        print("No hay registros nuevos que cumplan los requisitos (tener mail o linkedin).")
        return

    # 4. Crear DataFrame y Concatenar
    df_nuevo = pd.DataFrame(nuevos_registros)
    df_final = pd.concat([df_original, df_nuevo], ignore_index=True)

    # 5. Guardar resultado
    nombre_salida = ruta_excel.replace('.xlsx', '_filtrado_contactos.xlsx')

    columnas_orden = ['EMPRESA', 'NOMBRE', 'MAIL', 'TELÉFONO', 'MAIL ENVIADO', 'WEB', 'CARGO', 'LINKEDIN']
    columnas_finales = [c for c in columnas_orden if c in df_final.columns]

    df_final[columnas_finales].to_excel(nombre_salida, index=False)

    print(f"--- PROCESO COMPLETADO ---")
    print(f"Empresas originales respetadas: {contador_ignoradas_por_existir}")
    print(f"Contactos descartados por falta de Mail/LinkedIn: {contador_sin_datos_contacto}")
    print(f"Nuevas filas añadidas: {len(df_nuevo)}")
    print(f"Archivo guardado: {nombre_salida}")

if __name__ == "__main__":
    #Configuración de rutas relativas (PyCharm)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)

    ruta_input_excel = os.path.join(root_dir, 'data', 'listado_contactos_alimentaria.xlsx')
    ruta_input_json = os.path.join(root_dir, 'exhibitor_webs.json')

    excel_enrich(ruta_input_excel, ruta_input_json)