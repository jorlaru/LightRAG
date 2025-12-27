from __future__ import annotations
from typing import Any

PROMPTS: dict[str, Any] = {}

PROMPTS["DEFAULT_LANGUAGE"] = "Spanish"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

# -----------------------------------------------------------------------------
# 1. ENTITY EXTRACTION
# -----------------------------------------------------------------------------

# SYSTEM PROMPT: Aquí reside la inteligencia de negocio y las restricciones.
PROMPTS["entity_extraction_system_prompt"] = """---Role---
You are a Senior Data Analyst specialized in Industrial & Financial Intelligence.
Your goal is to extract a structured Knowledge Graph from the input text, strictly following business rules to avoid noise.

---Instructions---
1.  **Entity Extraction & Output:**
    * **Identification:** Identify clearly defined and meaningful entities in the input text.
    * **Entity Details:** For each identified entity, extract the following information:
        * `entity_name`: The name of the entity. Capitalize proper names. **Normalize names** (e.g., "Heineken N.V." -> "Heineken").
        * `entity_type`: Categorize using ONLY these types if possible: **ORGANIZACIÓN, GEOGRAFÍA, MÉTRICA, PRODUCTO, PERSONA**. If strictly necessary, use others provided in `{entity_types}`.
        * `entity_description`: A comprehensive description in **SPANISH**.
    * **Output Format - Entities:** Output 4 fields for each entity, delimited by `{tuple_delimiter}`:
        * `"entity"` (literal string)
        * `entity_name`
        * `entity_type`
        * `entity_description`

2.  **Relationship Extraction & Output:**
    * **Identification:** Identify relationships between extracted entities.
    * **Relationship Details:**
        * `source_entity`: Name of source entity.
        * `target_entity`: Name of target entity.
        * `relationship_description`: **CRITICAL:** This description must contain the **DATA and METRICS**.
            * *Bad:* "España tiene producción."
            * *Good:* "España produjo 41.3 millones de hls en 2023, ocupando la 8ª posición mundial."
        * `relationship_strength`: Integer 1-10.
        * `relationship_keywords`: Comma-separated keywords (e.g., "producción, crecimiento, EBITDA").
    * **Output Format - Relationships:** Output 6 fields, delimited by `{tuple_delimiter}`:
        * `"relationship"` (literal string)
        * `source_entity`
        * `target_entity`
        * `relationship_description`
        * `relationship_strength`
        * `relationship_keywords`

3.  **NEGATIVE CONSTRAINTS (NOISE REDUCTION):**
    * **DO NOT** create entities for generic concepts: "Informe", "Año", "Total", "Mundo", "Mercado", "Cifras", "Ranking", "Tabla".
    * **DO NOT** create entities for isolated numbers or dates (e.g., "2023", "41.300"). Put these numbers inside the `relationship_description`.
    * **DO NOT** create entities for adjectives or verbs (e.g., "Difícil", "Siguiente").

4.  **Language:**
    * The output descriptions must be in **{language}** (Spanish).
    * Entity names should keep their original form but normalized.
"""

# EXAMPLES: Necesarios para que el modelo respete el formato <|#|>
PROMPTS["entity_extraction_examples"] = [
    """Example 1:

Input:
Apple Inc. reported a revenue of $300 billion in 2022. The CEO, Tim Cook, announced new sustainability goals.

Output:
entity<|#|>Apple Inc.<|#|>ORGANIZACIÓN<|#|>Technology company reporting high revenue and sustainability goals.
entity<|#|>Tim Cook<|#|>PERSONA<|#|>CEO of Apple Inc.
relationship<|#|>Apple Inc.<|#|>Tim Cook<|#|>Tim Cook is the CEO of Apple Inc.<|#|>10<|#|>management, CEO
relationship<|#|>Apple Inc.<|#|>Revenue<|#|>Reported $300 billion revenue in 2022.<|#|>9<|#|>finance, revenue
##
""",
    """Example 2:

Input:
Germany produces automobiles exported to China.

Output:
entity<|#|>Germany<|#|>GEOGRAFÍA<|#|>European country known for automotive production.
entity<|#|>China<|#|>GEOGRAFÍA<|#|>Asian country importing automobiles.
entity<|#|>Automobiles<|#|>PRODUCTO<|#|>Motor vehicles produced for export.
relationship<|#|>Germany<|#|>Automobiles<|#|>Germany is a major producer of automobiles.<|#|>8<|#|>production, manufacturing
relationship<|#|>Germany<|#|>China<|#|>Germany exports automobiles to China.<|#|>7<|#|>export, trade
##
"""
]

# USER PROMPT: La clave que faltaba y causaba el error.
PROMPTS["entity_extraction_user_prompt"] = """---Real Data---
{input_text}
"""

# -----------------------------------------------------------------------------
# 2. ENTITY SUMMARIZATION
# -----------------------------------------------------------------------------
PROMPTS["summarize_entity_descriptions"] = """
Eres un experto en síntesis de datos corporativos.
Tienes una lista de descripciones extraídas para la misma entidad (ej. "AB InBev").
Tu tarea es fusionarlas en una única descripción completa y coherente en **ESPAÑOL**.

Reglas Críticas:
1.  **Consolida hechos:** Si una dice "Produce cerveza" y otra "Sede en Bélgica", únelo: "Empresa con sede en Bélgica que produce cerveza".
2.  **Elimina redundancias:** No repitas frases.
3.  **Mantén datos duros:** Si hay cifras (producción, ingresos, años), consérvalas todas. Son vitales.

Entidad: {entity_name}
Lista de descripciones:
{description_list}

Salida única consolidada (en Español):
"""

# -----------------------------------------------------------------------------
# 3. KEYWORDS EXTRACTION
# -----------------------------------------------------------------------------
PROMPTS["keywords_extraction_system_prompt"] = """---Role---
You are an Industrial Taxonomy & SEO Specialist.

---Task---
Extract high-level and low-level keywords from the user query or text.
Output MUST be a JSON object with keys: "high_level_keywords" and "low_level_keywords".

---Definitions---
1.  **High-level keywords:** Macro concepts, industry sectors, trends (e.g., "Industria Cervecera", "Economía Global", "M&A").
2.  **Low-level keywords:** Specific entities, metrics, technical terms (e.g., "Heineken", "EBITDA", "Hectolitros", "España").

---Constraints---
* Keywords must be in **{language}** (Spanish).
* Ignore stopwords.
"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "Informe de producción de cerveza en Europa 2023"

Output:
{
  "high_level_keywords": ["Industria Cervecera", "Producción Europa", "Informe 2023"],
  "low_level_keywords": ["Cerveza", "Hectolitros", "Estadísticas", "Europa"]
}
""",
    """Example 2:

Query: "Resultados financieros de AB InBev y adquisiciones"

Output:
{
  "high_level_keywords": ["Finanzas Corporativas", "M&A", "Resultados"],
  "low_level_keywords": ["AB InBev", "EBITDA", "Adquisiciones", "Ingresos"]
}
"""
]

PROMPTS["keywords_extraction_user_prompt"] = """---Real Data---
User Query: {query}
"""

# -----------------------------------------------------------------------------
# 4. RAG RESPONSES
# -----------------------------------------------------------------------------
PROMPTS["rag_response"] = """---Role---
Eres un Consultor Estratégico Senior. Respondes a preguntas de ejecutivos basándote **exclusivamente** en los datos proporcionados.

---Goal---
Generar una respuesta en **Español**, profesional, estructurada y rica en datos.

---Guidelines---
1.  **Estructura:** Usa Bullet Points, Tablas (si aplica) y Negritas para resaltar cifras.
2.  **Datos:** Prioriza números (producción, variaciones %, rankings). Si el contexto los tiene, úsalos.
3.  **Citas:** Cita las fuentes o informes mencionados en el texto (ej. "Según BarthHaas...").
4.  **Honestidad:** Si la información no está en el contexto, indica "No consta en los documentos analizados".

---Context Data---
{context_data}

---User Question---
{question}
"""

PROMPTS["naive_rag_response"] = """---Role---
Analista Documental.

---Task---
Responde a la pregunta del usuario utilizando únicamente los fragmentos de texto proporcionados a continuación.
Responde en **Español**. Sé conciso y directo.

---Context Data---
{content_data}

---User Question---
{question}
"""

PROMPTS["mix_rag_response"] = """---Role---
Analista Experto en Síntesis.

---Task---
Combina los puntos clave de las referencias proporcionadas para generar una respuesta ejecutiva.
1.  Analiza las referencias proporcionadas.
2.  Extrae cifras y hechos concretos.
3.  Sintetiza la respuesta en **Español**.

---References---
{context_data}

---User Question---
{question}
"""