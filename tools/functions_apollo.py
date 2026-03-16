import os
import json
import httpx
from typing import Any, Dict
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
# URL ACTUALIZADA SEGÚN EL ERROR 422
APOLLO_URL = "https://api.apollo.io/v1/mixed_people/api_search"
#URL de eriquecimiento por ID
APOLLO_BULK_MATCH_URL = "https://api.apollo.io/api/v1/people/bulk_match"

TARGET_TITLES = [
    "Director Comercial", "Director de Marketing", "Commercial Director",
    "Marketing Director", "Chief Commercial Officer", "CCO", "CMO",
    "Chief Marketing Officer", "Head of Sales", "Head of Marketing",
    "VP of Sales", "VP of Marketing", "Sales Director",
    "Gerente Comercial", "Gerente de Marketing", "Sales Manager", "Marketing Manager"
]


def extract_clean_domain(url: str) -> str:
    if not url or url == "null":
        return ""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.strip().lower()
    except Exception:
        return ""


async def enrich_existing_json_with_apollo(
        *,
        file_path: str = "exhibitor_webs.json",
        verbose: bool = True
) -> Dict[str, Any]:
    if not APOLLO_API_KEY:
        raise ValueError("APOLLO_API_KEY no encontrada en el .env")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    key_name = "results" if "results" in data else "rows"
    items = data.get(key_name, [])

    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx, entry in enumerate(items):
            web_url = entry.get("web_empresa")
            domain = extract_clean_domain(web_url)

            if not domain:
                entry["apollo_ids"] = []
                continue

            if verbose:
                print(f"[{idx + 1}/{len(items)}] 🎯 Consultando en nuevo endpoint: '{domain}'")

            # Estructura para el nuevo endpoint api_search
            payload = {
                "q_organization_domains": domain,
                "person_titles": TARGET_TITLES,
                "page": 1,
                "per_page": 5
            }

            try:
                response = await client.post(
                    APOLLO_URL,
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    apollo_data = response.json()
                    # En el nuevo endpoint, a veces la clave es 'people' o 'contacts'
                    # pero usualmente mantienen 'people' en api_search
                    people = apollo_data.get("people", [])
                    ids = [p.get("id") for p in people if p.get("id")]
                    entry["apollo_ids"] = ids
                    if verbose: print(f"   ✅ Encontrados: {len(ids)}")
                else:
                    entry["apollo_ids"] = []
                    if verbose: print(f"   ⚠️ Error {response.status_code}: {response.text}")

            except Exception as e:
                entry["apollo_ids"] = []
                if verbose: print(f"   ❌ Error: {e}")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


async def enrich_contacts_details(
        *,
        file_path: str = "exhibitors_webs.json",
        verbose: bool = True
) -> Dict[str, Any]:
    if not APOLLO_API_KEY:
        raise ValueError("APOLLO_API_KEY no encontrada en el .env")

    # 1. Cargar el archivo
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise Exception(f"No se encontró el archivo: {file_path}")

    items = data.get("results" if "results" in data else "rows", [])

    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }

    if verbose:
        print(f"🚀 Iniciando fase de Bulk Match para {len(items)} empresas...")

    async with httpx.AsyncClient(timeout=60.0) as client:
        for idx, entry in enumerate(items):
            ids = entry.get("apollo_ids", [])

            # Si no hay IDs, saltamos
            if not ids:
                entry["contacts_info"] = []
                continue

            if verbose:
                print(f"[{idx + 1}/{len(items)}] 🔍 Procesando {len(ids)} IDs para: {entry.get('exhibitorName')}")

            # 2. Preparar el payload con TODOS los IDs de esta empresa
            # Formato esperado: "details": [{"id": "id1"}, {"id": "id2"}]
            details_list = [{"id": i} for i in ids]

            payload = {
                "details": details_list,
                "reveal_personal_emails": True,
                "reveal_phone_number": False
            }

            try:
                response = await client.post(
                    APOLLO_BULK_MATCH_URL,
                    json=payload,
                    headers=headers
                )

                if response.status_code == 200:
                    res_data = response.json()
                    matches = res_data.get("matches", [])

                    contacts_extracted = []
                    for m in matches:
                        # Verificación de datos: solo guardamos si tiene nombre
                        if m:
                            contacts_extracted.append({
                                "name": m.get("name"),
                                "title": m.get("title"),
                                "email": m.get("email")
                            })

                    # Actualizar el registro
                    entry["contacts_info"] = contacts_extracted

                    if verbose:
                        if contacts_extracted:
                            print(f"   ✅ Éxito: Se obtuvieron {len(contacts_extracted)} contactos reales.")
                        else:
                            print(f"   ⚠️ Apollo devolvió 200 pero sin matches (revisa créditos).")

                else:
                    entry["contacts_info"] = []
                    if verbose:
                        print(f"   ❌ Error {response.status_code} en Apollo: {response.text}")

            except Exception as e:
                entry["contacts_info"] = []
                if verbose:
                    print(f"   ❌ Error de conexión: {str(e)}")

    # 3. Guardar cambios
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"💾 Proceso finalizado. Archivo '{file_path}' actualizado.")

    return data