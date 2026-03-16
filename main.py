import uvicorn
from agents import RunConfig
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from tools.functions import *
from tools.functions_apollo import enrich_existing_json_with_apollo
from tools.functions_openai import enrich_exhibitors_csv_one_by_one
from tools.openai_agent import consulta_empresa
import os
from dotenv import load_dotenv
from tools.functions_openai import execute_web_test_workflow
from tools.functions_apollo import enrich_contacts_details

load_dotenv()

class WebTestRequest(BaseModel):
    input_file: str = "exhibitor_enriched_test.json"
    output_file: str = "exhibitor_webs.json"

class Exhibitor(BaseModel):
    exhibitorName: Optional[str] = None
    standLocation: Optional[str] = None
    sectorId: Optional[str] = None
    sectorName: Optional[str] = None
    mainImage: Optional[str] = None
    description_es: Optional[str] = None #None para indicar que puede estar vacio

class EnrichRequest(BaseModel):
    csv_path: str = "exhibitors.csv"
    out_json_path: str = "exhibitors_enriched.json"
    out_csv_path: str | None = "exhibitors_enriched.csv"
    name_col: str = "exhibitorName"
    delay_seconds: float = 0.0
    verbose: bool = True

class CleanRequest(BaseModel):
    csv_path: str = "exhibitors.csv"
    out_csv_path: str = "exhibitors_cleaned.csv"

ruta_csv = "exhibitors_test.csv"

app = FastAPI(
    tittle = "API Exhibitors",
    description="Recibe datos de un csv",
    version="1.0.0"
)


@app.post("/csv/clean_missing_description")
async def clean_csv(req: CleanRequest):
    result = clean_csv_without_description(
        csv_path=req.csv_path,
        out_csv_path=req.out_csv_path,
        verbose=True
    )
    return result

@app.post("/enrich_exhibitors/run")
async def enrich_exhibitors_run(req: EnrichRequest):
    # aquí “el botón”: llamas al endpoint y se ejecuta
    result = await enrich_exhibitors_csv_one_by_one(
        csv_path=req.csv_path,
        out_json_path=req.out_json_path,
        out_csv_path=req.out_csv_path,
        name_col=req.name_col,
        agent=consulta_empresa,
        run_config=RunConfig(trace_metadata={
            "trace_source": "api-run",
            "workflow_id": "enrich_exhibitors_csv"
        }),
        delay_seconds=req.delay_seconds,
        verbose=req.verbose
    )
    return {
        "status": "success",
        "count_total": result["count_total"],
        "count_errors": result["count_errors"],
        "out_json_path": req.out_json_path,
        "out_csv_path": req.out_csv_path,
        # OJO: si el CSV es grande, esto puede ser enorme.
        # Si quieres, quita rows del response y deja solo resumen.
        "rows_preview": result["rows"][:10],
        "errors": result["errors"],
    }

@app.post("/test/run_antonio_workflow")
async def run_antonio_test(req: WebTestRequest):
    result = await execute_web_test_workflow(
        input_json_path=req.input_file,
        out_json_path=req.output_file,
        verbose=True
    )
    return {
        "status": "Prueba completada",
        "archivo_generado": req.output_file,
        "total": len(result["results"])
    }


@app.post("/enrich/apollo_ids")
async def run_apollo_enrichment():
    try:
        # Esto modificará directamente "exhibitor_webs.json"
        await enrich_existing_json_with_apollo(
            file_path="exhibitor_webs.json",
            verbose=True
        )
        return {
            "status": "success",
            "message": "Archivo exhibitor_webs.json enriquecido con IDs de Apollo"
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/enrich/apollo_contacts_details")
async def run_apollo_contacts_enrichment():
    try:
        # ASEGÚRATE DE QUE ESTE NOMBRE COINCIDA CON EL PASO ANTERIOR
        # Si tu archivo se llama exhibitor_webs.json (sin s), quita la s aquí:
        await enrich_contacts_details(file_path="exhibitor_webs.json")
        return {
            "status": "success",
            "message": "Contactos enriquecidos correctamente."
        }
    except Exception as e:
        # Esto te dirá exactamente qué nombre de archivo intentó abrir y falló
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
