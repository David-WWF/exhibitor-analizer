import os
from pydantic import BaseModel
from agents import Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace

# El esquema que ya tienes
class AntonioElBuscadorDeWebsSchema(BaseModel):
  web_empresa: str
  score_web: str

# El agente tal cual lo definiste
antonio_el_buscador_de_webs = Agent(
  name="Antonio, el buscador de Webs",
  instructions="""Actúa como un Agente de Verificación de Datos en Tiempo Real. Tu objetivo es encontrar la URL corporativa oficial de la empresa que se te proporciona.

INSTRUCCIONES CRÍTICAS DE BÚSQUEDA:
Búsqueda Externa Obligatoria: No intentes adivinar la URL por el nombre de la empresa. Ejecuta una búsqueda en Google/Bing y analiza los 5 primeros resultados orgánicos.
Prioridad de Resultados: Busca específicamente el dominio que aparezca asociado a la empresa en directorios fiables (como Google Maps, LinkedIn oficial o e-Informa) antes de darlo por bueno.
Protocolo de Validación (Matching):
Una vez tengas una URL, busca en su 'Aviso Legal', 'Contacto' o 'Pie de página'.
Comprueba que el Nombre Fiscal o la Sede Social coincidan con la empresa solicitada.
Si el dominio es familiapuerto.com pero la empresa real usa lopezpuerto.com, descarta el primero por ser una coincidencia falsa.
Manejo de Errores: Si la URL encontrada no carga, está en construcción o no tiene relación directa con la actividad de la empresa, devuelve null.""",
  model="gpt-4.1",
  output_type=AntonioElBuscadorDeWebsSchema,
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)

class WorkflowInput(BaseModel):
  input_as_text: str

# Tu función motor run_workflow
async def run_workflow(workflow_input: WorkflowInput):
  with trace("Antonio, el buscador de webs"):
    workflow = workflow_input.model_dump()
    conversation_history: list[TResponseInputItem] = [
      {
        "role": "user",
        "content": [
          {
            "type": "input_text",
            "text": workflow["input_as_text"]
          }
        ]
      }
    ]
    antonio_el_buscador_de_webs_result_temp = await Runner.run(
      antonio_el_buscador_de_webs,
      input=[*conversation_history],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69b7c7b6423c8190afdf0b34e013c14504367fb63c85f286"
      })
    )

    antonio_el_buscador_de_webs_result = {
      "output_text": antonio_el_buscador_de_webs_result_temp.final_output.json(),
      "output_parsed": antonio_el_buscador_de_webs_result_temp.final_output.model_dump()
    }
    return antonio_el_buscador_de_webs_result