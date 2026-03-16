import os
import json
import httpx
import asyncio
from typing import Any, Dict
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# Configuración de URLs y API Key
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
APOLLO_SEARCH_URL = "https://api.apollo.io/v1/mixed_people/api_search"
APOLLO_BULK_MATCH_URL = "https://api.apollo.io/api/v1/people/bulk_match"

# Títulos estratégicos para la búsqueda
TARGET_TITLES = [
    "Director Comercial", "Director de Marketing", "Commercial Director",
    "Marketing Director", "Chief Commercial Officer", "CCO", "CMO",
    "Chief Marketing Officer", "Head of Sales", "Head of Marketing",
    "VP of Sales", "VP of Marketing", "Sales Director",
    "Gerente Comercial", "Gerente de Marketing", "Sales Manager", "Marketing Manager"
]


def extract_clean_domain(url: str) -> str:
    """Extrae el dominio limpio (ej: empresa.com) de una URL completa."""
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


async def get_apollo_ids(
        *,
        file_path: str = "exhibitor_webs.json",
        verbose: bool = True
) -> Dict[str, Any]:
    """PASO 1: Busca personas por dominio y guarda sus IDs en el JSON."""
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
            # Control de Rate Limit: 40 peticiones -> 60 seg de pausa
            if idx > 0 and idx % 40 == 0:
                if verbose: print(f"⏳ Pausa técnica (Rate Limit) de 60s...")
                await asyncio.sleep(60)

            domain = extract_clean_domain(entry.get("web_empresa"))
            if not domain:
                entry["apollo_ids"] = []
                continue

            if verbose: print(f"[{idx + 1}/{len(items)}] 🎯 Buscando IDs: {domain}")

            payload = {
                "q_organization_domains": domain,
                "person_titles": TARGET_TITLES,
                "page": 1,
                "per_page": 5
            }

            try:
                response = await client.post(APOLLO_SEARCH_URL, json=payload, headers=headers)
                if response.status_code == 200:
                    people = response.json().get("people", [])
                    entry["apollo_ids"] = [p.get("id") for p in people if p.get("id")]
                else:
                    entry["apollo_ids"] = []
            except Exception:
                entry["apollo_ids"] = []

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data

# Rellena e Json con los datos de contacto, solo si hay ids que comprobar
async def enrich_contacts_details(
        *,
        file_path: str = "exhibitor_webs.json",
        verbose: bool = True
) -> Dict[str, Any]:
    """
    PASO 2: Revela Email, Nombre y Cargo.
    Guarda en el archivo JSON después de cada petición exitosa para máxima seguridad.
    """
    if not APOLLO_API_KEY:
        raise ValueError("APOLLO_API_KEY no encontrada en el .env")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró {file_path}")
        return {}

    key_name = "results" if "results" in data else "rows"
    items = data.get(key_name, [])

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        for idx, entry in enumerate(items):
            ids = entry.get("apollo_ids", [])

            # 1. Saltos preventivos (Ahorro de créditos y tiempo)
            if not ids:
                continue

            # Si ya tiene información, no volvemos a preguntar a la API
            if entry.get("contacts_info") and len(entry["contacts_info"]) > 0:
                if verbose: print(f"[{idx + 1}/{len(items)}] ⏩ Ya enriquecido: {entry.get('exhibitorName')}")
                continue

            if verbose: print(f"[{idx + 1}/{len(items)}] 🔍 Procesando: {entry.get('exhibitorName')}")

            payload = {
                "details": [{"id": i} for i in ids],
                "reveal_personal_emails": True,
                "reveal_phone_number": False
            }

            # 2. Lógica de petición con Reintento para Error 429
            max_retries = 1
            attempts = 0
            success = False

            while attempts <= max_retries and not success:
                try:
                    response = await client.post(APOLLO_BULK_MATCH_URL, json=payload, headers=headers)

                    if response.status_code == 200:
                        matches = response.json().get("matches", [])
                        entry["contacts_info"] = [
                            {"name": m.get("name"), "title": m.get("title"), "email": m.get("email")}
                            for m in matches if m
                        ]
                        if verbose: print(f"   ✅ Datos obtenidos y guardados.")

                        # --- GUARDADO INMEDIATO EN CADA PASO ---
                        with open(file_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)

                        success = True

                    elif response.status_code == 429:
                        attempts += 1
                        wait_time = 120  # 2 minutos de enfriamiento
                        if verbose: print(f"   ⚠️ Error 429 (Rate Limit). Pausa de emergencia de {wait_time}s...")
                        await asyncio.sleep(wait_time)

                    else:
                        if verbose: print(f"   ⚠️ Error API {response.status_code}: {response.text}")
                        break

                except Exception as e:
                    if verbose: print(f"   ❌ Error de red: {e}")
                    break

                # Pausa de cortesía para mantener un ritmo estable (< 40 peticiones/min)
                await asyncio.sleep(1.6)

    if verbose: print(f"💾 Proceso completado con éxito. Todo el progreso ha sido guardado.")
    return data