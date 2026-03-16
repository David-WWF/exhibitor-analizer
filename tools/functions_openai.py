import asyncio
import json
from typing import Any, Dict, Optional

import pandas as pd
from agents import Runner, RunConfig, trace
from tools.buscador_webs_agent import run_workflow, WorkflowInput



async def enrich_exhibitors_csv_one_by_one(
    *,
    csv_path: str,
    out_json_path: str = "exhibitors_enriched.json",
    out_csv_path: Optional[str] = "exhibitors_enriched.csv",
    name_col: str = "exhibitorName",
    agent=None,  # tu Agent: consulta_empresa
    run_config: Optional[RunConfig] = None,
    delay_seconds: float = 0.0,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Lee el CSV, llama al agente uno por uno con exhibitorName,
    imprime el progreso y la respuesta del agente, y guarda JSON (y opcional CSV).
    """
    if agent is None:
        raise ValueError("Debes pasar el agent en `agent=` (ej: agent=consulta_empresa).")

    df = pd.read_csv(csv_path)

    if name_col not in df.columns:
        raise ValueError(f"No existe la columna '{name_col}' en el CSV. Columnas: {list(df.columns)}")

    #TODO falta función que sustituya un valor NaN por null

    # columnas destino
    for col in ("company_employees", "average_billing", "fiability_score", "revenue_score", "employees_score", "expansion_score",
                "multilanguage_score", "innovation_score", "brand_architecture_score", "retail_presence_score", "total_score", "priority"):
        if col not in df.columns:
            df[col] = None

    enriched_rows = []
    errors = []

    with trace("Enrich Exhibitors (API run)"):
        for idx, row in df.iterrows():
            exhibitor_name = row.get(name_col)
            exhibitor_name_str = "" if pd.isna(exhibitor_name) else str(exhibitor_name).strip()

            if not exhibitor_name_str:
                errors.append({"row_index": int(idx), "error": f"{name_col} vacío"})
                enriched_rows.append(row.to_dict())
                continue

            if verbose:
                print(f"\n[ENRICH] ({idx+1}/{len(df)}) Empresa => {exhibitor_name_str}")

            prompt = (

                f"Compañía: {exhibitor_name_str}"
            )

            try:
                result = await Runner.run(
                    agent,
                    input=prompt,          # puedes pasar string directo
                    run_config=run_config,
                )

                final = result.final_output

                # Intento: parsed (Pydantic) -> dict
                parsed: Dict[str, Any] = {}
                if hasattr(final, "model_dump"):
                    parsed = final.model_dump()
                elif isinstance(final, dict):
                    parsed = final
                elif isinstance(final, str):
                    # Si viene como string json
                    try:
                        parsed = json.loads(final)
                    except Exception:
                        parsed = {"raw": final}
                else:
                    parsed = {"raw": str(final)}

                # Extraer
                employees_val = parsed.get("company_employees")
                billing_val = parsed.get("average_billing")
                fiability_score = parsed.get("fiability_score")
                revenue_score = parsed.get("revenue_score")
                employees_score = parsed.get("employees_score")
                expansion_score = parsed.get("expansion_score")
                multilanguage_score = parsed.get("multilanguage_score")
                innovation_score = parsed.get("innovation_score")
                brand_architecture_score = parsed.get("brand_architecture_score")
                retail_presence_score = parsed.get("retail_presence_score")
                total_score = parsed.get("total_score")
                priority = parsed.get("priority")

                # Prints de trazado
                if verbose:
                    print("[AGENT RETURN] parsed =>", parsed)

                # Guardar en DF
                df.at[idx, "company_employees"] = employees_val
                df.at[idx, "average_billing"] = billing_val
                df.at[idx, "fiability_score"] = fiability_score
                df.at[idx, "revenue_score"] = revenue_score
                df.at[idx, "employees_score"] = employees_score
                df.at[idx, "expansion_score"] = expansion_score
                df.at[idx, "multilanguage_score"] = multilanguage_score
                df.at[idx, "innovation_score"] = innovation_score
                df.at[idx, "brand_architecture_score"] = brand_architecture_score
                df.at[idx, "retail_presence_score"] = retail_presence_score
                df.at[idx, "total_score"] = total_score
                df.at[idx, "priority"] = priority

                row_out = row.to_dict()
                row_out["company_employees"] = employees_val
                row_out["average_billing"] = billing_val
                row_out["fiability_score"] = fiability_score
                row_out["revenue_score"] = revenue_score
                row_out["employees_score"] = employees_score
                row_out["expansion_score"] = expansion_score
                row_out["multilanguage_score"] = multilanguage_score
                row_out["innovation_score"] = innovation_score
                row_out["brand_architecture_score"] = brand_architecture_score
                row_out["retail_presence_score"] = retail_presence_score
                row_out["total_score"] = total_score
                row_out["priority"] = priority
                enriched_rows.append(row_out)

            except Exception as e:
                err = {"row_index": int(idx), "exhibitorName": exhibitor_name_str, "error": str(e)}
                errors.append(err)
                if verbose:
                    print("[ERROR]", err)
                enriched_rows.append(row.to_dict())

            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

    payload = {
        "source_csv": csv_path,
        "count_total": int(len(df)),
        "count_errors": int(len(errors)),
        "errors": errors,
        "rows": enriched_rows,
    }

    # Guardar JSON
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Guardar CSV enriquecido (si quieres)
    if out_csv_path:
        df.to_csv(out_csv_path, index=False)

    return payload

# Nueva funcion del agente Antonio
async def execute_web_test_workflow(
        *,
        input_json_path: str,
        out_json_path: str = "exhibitor_webs.json",
        verbose: bool = True
) -> Dict[str, Any]:
    # 1. Leer el archivo de prueba (exhibitor_enriched_test.json)
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = data.get("rows", [])
    test_results = []

    if verbose:
        print(f"🚀 Iniciando prueba con {len(rows)} registros...")

    # 2. Iterar y llamar a TU función run_workflow
    for idx, row in enumerate(rows):
        name = row.get("exhibitorName", "").strip()
        if not name: continue

        if verbose:
            print(f"[{idx + 1}/{len(rows)}] Procesando: {name}")

        try:
            # Llamamos a tu función respetando su WorkflowInput
            result = await run_workflow(WorkflowInput(input_as_text=name))

            # Extraemos los datos del "output_parsed" que genera tu función
            parsed = result["output_parsed"]

            test_results.append({
                "exhibitorName": name,
                "web_empresa": parsed.get("web_empresa"),
                "score_web": parsed.get("score_web")
            })
        except Exception as e:
            if verbose: print(f"❌ Error en {name}: {e}")
            continue

    # 3. Guardar en el NUEVO archivo JSON sin modificar el original
    output_data = {
        "test_source": input_json_path,
        "results": test_results
    }

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    return output_data