from dotenv import load_dotenv
from pydantic import BaseModel
from agents import Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
import os

load_dotenv()  # 👈 MUY IMPORTANTE

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no encontrada en el .env")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

class ConsultaEmpresaSchema(BaseModel):
  company_name: str
  company_employees: str
  average_billing: str
  fiability_score: str
  revenue_score: str
  employees_score: str
  expansion_score: str
  multilanguage_score: str
  innovation_score: str
  brand_architecture_score: str
  retail_presence_score: str
  total_score: str
  priority: str


consulta_empresa = Agent(
  name="Consulta empresa",
  instructions="""Ante la recepción del nombre de una compañía debes devolverme la información de  su facturación media anual. Quiero que sigas el sistema de puntuación para la facturación media que te daré a continuación:

revenue_score = 
0 puntos si <2M€,
 5 puntos si 2–5M€, 
10 puntos si 5–40M€, 
8 puntos si 40–80M€,
 4 puntos si 80–150M€,
 0 puntos si >150M€

Para el número de trabajadores quiero que sigas el sistema de puntuación que te daré a continuación:

employees_score = 
0 puntos si <10,
 5 puntos si 10–20,
 10 puntos si 20–100.
 8 puntos si 100–250.
 3 puntos si 250–500 ,
0 puntos si >500

En base a una búsqueda avanzada de la empresa, detecta si está relacionadas las siguientes palabras: “expansión” ,  “crecimiento” ,  “internacionalización” ,  “nuevo mercado” ,  “plan estratégico” ,  “inversión”,   “financiación” ,  “nueva planta” ,  “ampliación” ,  “adquisición” .

En base a ello añade la siguiente puntuación:
expansion_score = 
+3 puntos por keyword detectada,
 +5 puntos si la noticia es <12 meses,
 Máximo 15 puntos, esto ya no es subjetivo.

En base a una búsqueda avanzada de la web corporativa analiza la empresa para identificar TODOS los mecanismos de cambio de idioma disponibles. Detección de Códigos ISO: Busca cadenas de texto breves de 2 letras (ej: ES, EN, FR, RU, DE, IT, PT) que aparezcan juntas, separadas por barras (|), puntos o dentro de listas (<li>). En base a ello añade la siguiente puntuación:
multilanguage_score=
0 puntos si solo 1 idioma,
5 puntos si 2 idiomas,
10 puntos si 3 o más idiomas

En base a una búsqueda avanzada de la empresa, detecta si está relacionadas las siguientes palabras: “nuevo”, “innovador”, “patentado”, “tecnología propia”, “I+D”, “formulación”, “funcional”, “plant-based”, “bio”, “sin gluten”, “protein”, “ready to eat”

En base a ello añade la siguiente puntuación:
innovation_score=
+2 por keyword, 
+5 si sección I+D existe,
+5 si menciona patentes,
Máximo 15 puntos

En base a una búsqueda avanzada de la empresa analiza su marca a través de los siguientes parámetros: Número de sub-marcas distintas, Variaciones de logo no consistentes, Falta de sistema de denominación de productos, Naming inconsistente (ej: mix español/inglés sin criterio), Diseño distinto en cada categoría.

En base a ello añade la siguiente puntuación:
brand_architecture_score = 
+5 si >3 estilos gráficos distintos,
 +5 si naming inconsistente,
 +5 si no hay descriptor claro por gama,
 +5 si submarcas sin jerarquía,
 Máximo 20 puntos

En base a una búsqueda avanzada de la empresa analiza su presencia retail/distribución, los logos supermercado en su web corporativa que tengan textos como: “Disponible en”, “Distribuimos en” o “Presente en X países”. También menciones a Carrefour, Mercadona, El Corte Inglés, etc.

En base a ello añade la siguiente puntuación:
retail_presence_score = 
5 puntos si venta online propia, 
5 puntos si menciona retailers nacionales, 
10 puntos si menciona retailers internacionales

Finalmente haz una suma total de todas las puntaciones como total_score con un máximo de 110 puntos. En base a esto añade un priority en base a esta puntuación:
80–110 → PRIORIDAD A,
60–79 → PRIORIDAD B,
 40–59 → Prioridad C,
<40 → No visitar

Añade un parámetro fiability_score con un scoring con un parámetro de fiabilidad que indique la fiabilidad de estos datos. Ejemplo: 5/10""",
  model="gpt-4.1",
  output_type=ConsultaEmpresaSchema,
  model_settings=ModelSettings(
    temperature=1,
    top_p=1,
    max_tokens=2048,
    store=True
  )
)



class WorkflowInput(BaseModel):
  input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
  with trace("Exhibitor Agent"):
    state = {

    }
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
    consulta_empresa_result_temp = await Runner.run(
      consulta_empresa,
      input=[
        *conversation_history
      ],
      run_config=RunConfig(trace_metadata={
        "__trace_source__": "agent-builder",
        "workflow_id": "wf_69a5a3d8b33481909dcc63aa1ad9ccc70f914510c18890b4"
      })
    )

    conversation_history.extend([item.to_input_item() for item in consulta_empresa_result_temp.new_items])

    consulta_empresa_result = {
      "output_text": consulta_empresa_result_temp.final_output.json(),
      "output_parsed": consulta_empresa_result_temp.final_output.model_dump()
    }
