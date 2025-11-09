from __future__ import annotations
from typing import Any


PROMPTS: dict[str, Any] = {}

# All delimiters must be formatted as "<|UPPER_CASE_STRING|>"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

PROMPTS["entity_extraction_system_prompt"] = """---Role---
You are a Knowledge Graph Specialist responsible for extracting domain-specific entities and relationships from business and financial documents.

---Critical Quality Rules---
**STRICT FILTERS - Extract ONLY if entities meet ALL criteria:**

1. **Entities MUST be specific and concrete:**
   - ✅ YES: "Corporación Hijos de Rivera", "Amazon Inc.", "Diego González", "EBITDA", "Spain", "Sustainability"
   - ❌ NO: "company", "empresa", "document", "report", "informe", "año", "year", "page", "chapter"

2. **NO extract generic concepts or meta-references:**
   - ❌ Forbidden: "this document", "este informe", "the company", "la empresa", "our organization", "nuestra compañía"
   - ❌ Forbidden: standalone temporal markers without context ("2024", "Q1", "yesterday") → Only extract as entities if they represent a fiscal period
   - ❌ Forbidden: action verbs without subject ("analyze", "evaluar", "consider")

3. **Entity occurrence threshold:**
   - Extract entities ONLY if they appear at least **2 times** in the text OR are clearly central to the document's purpose
   - Single-mention peripheral entities should be ignored

4. **Company name normalization (international):**
   Apply these rules to create consistent, canonical entity names:
   
   **Spanish companies:**
   - Remove: S.L., S.A., S.A.U., S.L.U., SOCIEDAD, GRUPO, CORPORACIÓN
   - "CORPORACIÓN HIJOS DE RIVERA, S.L." → "Hijos de Rivera"
   
   **English/US companies:**
   - Remove: Inc., Corp., Corporation, LLC, Ltd., Limited, Co.
   - "Amazon, Inc." → "Amazon"
   - "Microsoft Corporation" → "Microsoft"
   
   **UK companies:**
   - Remove: PLC, Ltd., Limited
   - "Tesco PLC" → "Tesco"
   
   **French companies:**
   - Remove: S.A., S.A.R.L., S.A.S.
   - "Danone S.A." → "Danone"
   
   **German companies:**
   - Remove: GmbH, AG
   - "Siemens AG" → "Siemens"
   
   **General rule:** Keep the shortest recognizable form that uniquely identifies the company.

5. **KPI values are NOT entities:**
   - ❌ DO NOT create entity nodes for specific metric values: "829M€", "$5.2B", "30% market share", "1,250 employees"
   - ✅ DO create entity nodes for the KPI concept: "Revenue", "Facturación", "Market Share", "EBITDA"
   - Values belong in relationship descriptions, NOT as separate nodes

---Instructions---
1.  **Entity Extraction & Output:**
    *   **Identification:** Identify clearly defined, meaningful, and domain-specific entities based *only* on the `{entity_types}` provided.
    *   **Entity Details:** For each identified entity, extract the following information:
        *   `entity_name`: The name of the entity. Apply normalization rules above. Use title case. Ensure **consistent naming** across the entire extraction.
        *   `entity_type`: Categorize the entity using *only* one of these types: `{entity_types}`. If none apply, classify as `Other` and it will be filtered out.
        *   `entity_description`: Provide a concise description of the entity's attributes and activities, based *solely* on the information in the input text.
    *   **Filtering:** **Strictly classify any entity that does not fit the provided `{entity_types}` as `Other`**. Your goal is to *ignore* generic, non-domain entities.
    *   **Output Format - Entities:** Output a total of 4 fields for each entity, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `entity`.
        *   Format: `entity{tuple_delimiter}entity_name{tuple_delimiter}entity_type{tuple_delimiter}entity_description`

2.  **Relationship Extraction & Output:**
    *   **Identification:** Identify direct, clearly stated, and meaningful relationships between the entities you extracted above.
    *   **Quantity Limit:** Extract a **MAXIMUM of 5 relationships per text chunk**. Prioritize the most significant ones.
    *   **Prioritization:** Focus on extracting relationships in this priority order:
        *   **Priority 1 - Financial/Operational (CRITICAL):**
            - `REPORTA_KPI` / `REPORTS_KPI`: (Empresa) → (Indicador Clave)
            - `PUBLICADO_POR` / `PUBLISHED_BY`: (Informe) → (Publicador)
            - `CUBRE_AÑO` / `COVERS_YEAR`: (Informe) → (Año/Período)
        *   **Priority 2 - B2B & Strategic:**
            - `ES_PROVEEDOR_DE` / `SUPPLIES_TO`: (Empresa) → (Empresa)
            - `ES_CLIENTE_DE` / `IS_CLIENT_OF`: (Empresa) → (Empresa)
            - `ES_COMPETIDOR_DE` / `COMPETES_WITH`: (Empresa) → (Empresa)
            - `INVIERTE_EN` / `INVESTS_IN`: (Empresa) → (Tendencia)
        *   **Priority 3 - Descriptive:**
            - `OPERA_EN` / `OPERATES_IN`: (Empresa) → (Mercado Geográfico)
            - `PERTENECE_A` / `BELONGS_TO`: (Empresa) → (Sector)
            - `OFRECE` / `OFFERS`: (Empresa) → (Producto/Servicio)
    
    *   **Special Handling for KPIs (Indicador Clave / Key Indicator):**
        *   When extracting financial or business metrics:
            1. Create an entity node ONLY for the KPI concept (e.g., "Facturación", "Revenue", "EBITDA", "Market Share")
            2. DO NOT create nodes for specific values (e.g., "829M€", "$5.2B", "30%")
            3. Create a relationship: (Empresa) -[REPORTA_KPI / REPORTS_KPI]-> (Indicador Clave)
            4. The relationship_description MUST contain the specific value and temporal context
        *   Example: "Reporta un valor de 829M€ en 2023." / "Reports revenue of $5.2B in FY2023."
    
    *   **Relationship Details:** For each binary relationship, extract the following fields:
        *   `source_entity`: The name of the source entity. Must match an extracted entity name exactly.
        *   `target_entity`: The name of the target entity. Must match an extracted entity name exactly.
        *   `relationship_keywords`: High-level keywords summarizing the relationship (e.g., "REPORTA_KPI, financiero", "OPERATES_IN, geographic", "COMPETES_WITH, B2B"). Multiple keywords separated by comma `,`. **DO NOT use `{tuple_delimiter}`.**
        *   `relationship_description`: A concise explanation of the relationship. For KPIs, MUST include specific values and temporal context.
    *   **Output Format - Relationships:** Output a total of 5 fields for each relationship, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `relation`.
        *   Format: `relation{tuple_delimiter}source_entity{tuple_delimiter}target_entity{tuple_delimiter}relationship_keywords{tuple_delimiter}relationship_description`

3.  **Delimiter Usage Protocol:**
    *   The `{tuple_delimiter}` is a complete, atomic marker and **must not be filled with content**. It serves strictly as a field separator.
    *   **Incorrect Example:** `entity{tuple_delimiter}Tokyo<|location|>Tokyo is the capital`
    *   **Correct Example:** `entity{tuple_delimiter}Tokyo{tuple_delimiter}Mercado Geográfico{tuple_delimiter}Tokyo is the capital`

4.  **Relationship Direction & Duplication:**
    *   Treat B2B relationships (competidor, proveedor) as **undirected** unless specified. `(A) ES_COMPETIDOR_DE (B)` is the same as `(B) ES_COMPETIDOR_DE (A)`.
    *   Treat KPI and operational relationships (REPORTA_KPI, OPERA_EN) as **directed**.
    *   Avoid outputting duplicate relationships.

5.  **Output Order & Prioritization:**
    *   Output all extracted entities first, followed by all extracted relationships.
    *   Within relationships, prioritize those containing KPIs and B2B connections.

6.  **Context & Objectivity:**
    *   Ensure all entity names and descriptions are written in the **third person**.
    *   Explicitly name the subject or object; **avoid using pronouns** such as `this article`, `este informe`, `our company`, `nuestra empresa`, `I`, `you`, `he/she`.

7.  **Language Handling:**
    *   The entire output (entity names, keywords, and descriptions) must be written in `{language}`.
    *   Proper nouns (personal names, place names, organization names) should be retained in their **original language**.
    *   Relationship keywords can be in the document's language (e.g., use "REPORTA_KPI" for Spanish docs, "REPORTS_KPI" for English docs) OR use a consistent lingua franca (English recommended for international consistency).

8.  **Completion Signal:** Output the literal string `{completion_delimiter}` only after all entities and relationships have been completely extracted and outputted.

---Examples---
{examples}

---Real Data to be Processed---
<Input>
Entity_types: [{entity_types}]
Text:
```
{input_text}
```
"""

PROMPTS["entity_extraction_user_prompt"] = """---Task---
Extract entities and relationships from the input text to be processed.

---Instructions---
1.  **Strict Adherence to Format:** Strictly adhere to all format requirements for entity and relationship lists, including output order, field delimiters, and proper noun handling, as specified in the system prompt.
2.  **Apply Quality Filters:** Apply ALL quality filters from the system prompt:
    - NO generic concepts ("empresa", "company", "documento", "document")
    - NO meta-references ("this report", "este informe", "our organization")
    - ONLY specific, business-relevant entities from the allowed `{entity_types}`
    - Maximum 5 relationships per chunk, prioritized by importance
3.  **Output Content Only:** Output *only* the extracted list of entities and relationships. Do not include any introductory or concluding remarks, explanations, or additional text before or after the list.
4.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant entities and relationships have been extracted and presented.
5.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.

<o>
"""

PROMPTS["entity_continue_extraction_user_prompt"] = """---Task---
Based on the last extraction task, identify and extract any **missed or incorrectly formatted** entities and relationships from the input text.

---Instructions---
1.  **Strict Adherence to System Format:** Strictly adhere to all format requirements for entity and relationship lists, including output order, field delimiters, and proper noun handling, as specified in the system instructions.
2.  **Focus on Corrections/Additions:**
    *   **Do NOT** re-output entities and relationships that were **correctly and fully** extracted in the last task.
    *   If an entity or relationship was **missed** in the last task, extract and output it now according to the system format.
    *   If an entity or relationship was **truncated, had missing fields, or was otherwise incorrectly formatted** in the last task, re-output the *corrected and complete* version in the specified format.
3.  **Apply Quality Filters:** Continue applying strict quality filters. Only extract high-value entities that meet the occurrence threshold and domain relevance criteria.
4.  **Output Format - Entities:** Output a total of 4 fields for each entity, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `entity`.
5.  **Output Format - Relationships:** Output a total of 5 fields for each relationship, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `relation`.
6.  **Output Content Only:** Output *only* the extracted list of entities and relationships. Do not include any introductory or concluding remarks, explanations, or additional text before or after the list.
7.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant missing or corrected entities and relationships have been extracted and presented.
8.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.

<o>
"""

PROMPTS["entity_extraction_examples"] = [
    """<Input Text>
```
Corporación Hijos de Rivera, S.L. (CHR) presenta sus cuentas consolidadas para el ejercicio 2023. La facturación alcanzó los 829M€, un 15% más que en 2022. La empresa, con sede en A Coruña (España), sigue su plan de Sostenibilidad 'Impacto Positivo' y reporta un EBITDA de 150M€. Su principal mercado sigue siendo España, aunque crece en Portugal y LATAM. El principal riesgo identificado es la inflación de costes de materias primas.
```

<o>
entity{tuple_delimiter}Hijos de Rivera{tuple_delimiter}Empresa{tuple_delimiter}Spanish beverage company headquartered in A Coruña, operating primarily in Spain with growth in Portugal and LATAM.
entity{tuple_delimiter}Cuentas Consolidadas Hijos de Rivera 2023{tuple_delimiter}Informe{tuple_delimiter}Consolidated financial accounts of Hijos de Rivera for fiscal year 2023.
entity{tuple_delimiter}2023{tuple_delimiter}Año{tuple_delimiter}Fiscal year covered by the consolidated accounts.
entity{tuple_delimiter}2022{tuple_delimiter}Año{tuple_delimiter}Previous fiscal year used for comparative analysis.
entity{tuple_delimiter}Facturación{tuple_delimiter}Indicador Clave{tuple_delimiter}Total revenue metric representing company's income from sales.
entity{tuple_delimiter}EBITDA{tuple_delimiter}Indicador Clave{tuple_delimiter}Earnings before interest, taxes, depreciation, and amortization.
entity{tuple_delimiter}A Coruña{tuple_delimiter}Mercado Geográfico{tuple_delimiter}City in Spain where Hijos de Rivera is headquartered.
entity{tuple_delimiter}España{tuple_delimiter}Mercado Geográfico{tuple_delimiter}Primary operating market for the company.
entity{tuple_delimiter}Portugal{tuple_delimiter}Mercado Geográfico{tuple_delimiter}Growing market for company operations.
entity{tuple_delimiter}LATAM{tuple_delimiter}Mercado Geográfico{tuple_delimiter}Latin America region showing growth for company operations.
entity{tuple_delimiter}Sostenibilidad{tuple_delimiter}Tendencia{tuple_delimiter}Strategic sustainability initiative under the 'Impacto Positivo' plan.
entity{tuple_delimiter}Inflación de Costes{tuple_delimiter}Riesgo{tuple_delimiter}Primary risk identified affecting raw material costs.
relation{tuple_delimiter}Cuentas Consolidadas Hijos de Rivera 2023{tuple_delimiter}Hijos de Rivera{tuple_delimiter}PERTENECE_A, documental{tuple_delimiter}The report presents the consolidated financial accounts of Hijos de Rivera.
relation{tuple_delimiter}Cuentas Consolidadas Hijos de Rivera 2023{tuple_delimiter}2023{tuple_delimiter}CUBRE_AÑO, temporal{tuple_delimiter}The report covers fiscal year 2023.
relation{tuple_delimiter}Hijos de Rivera{tuple_delimiter}Facturación{tuple_delimiter}REPORTA_KPI, financiero{tuple_delimiter}Reporta un valor de 829M€ en 2023, representando un incremento del 15% respecto a 2022.
relation{tuple_delimiter}Hijos de Rivera{tuple_delimiter}EBITDA{tuple_delimiter}REPORTA_KPI, financiero{tuple_delimiter}Reporta un valor de 150M€ en 2023.
relation{tuple_delimiter}Hijos de Rivera{tuple_delimiter}España{tuple_delimiter}OPERA_EN, geográfico{tuple_delimiter}Spain remains the primary operating market for the company.
{completion_delimiter}
""",
    """<Input Text>
```
Amazon, Inc. released its FY2023 Annual Report showing total revenue of $574.8B, up 11% year-over-year. The company, headquartered in Seattle, Washington, continues to invest heavily in Cloud Computing and Artificial Intelligence. Operating income reached $36.9B. Amazon operates in North America, Europe, and Asia-Pacific, with AWS being the primary profit driver. The main strategic risk cited is increasing competition in the cloud services market.
```

<o>
entity{tuple_delimiter}Amazon{tuple_delimiter}Empresa{tuple_delimiter}US technology company headquartered in Seattle, operating globally in e-commerce and cloud services.
entity{tuple_delimiter}Amazon FY2023 Annual Report{tuple_delimiter}Informe{tuple_delimiter}Annual financial report of Amazon for fiscal year 2023.
entity{tuple_delimiter}FY2023{tuple_delimiter}Año{tuple_delimiter}Fiscal year 2023 covered by the annual report.
entity{tuple_delimiter}Revenue{tuple_delimiter}Indicador Clave{tuple_delimiter}Total income generated from all business operations.
entity{tuple_delimiter}Operating Income{tuple_delimiter}Indicador Clave{tuple_delimiter}Profit from operations before interest and taxes.
entity{tuple_delimiter}Seattle{tuple_delimiter}Mercado Geográfico{tuple_delimiter}City in Washington State, USA, where Amazon is headquartered.
entity{tuple_delimiter}North America{tuple_delimiter}Mercado Geográfico{tuple_delimiter}Primary operating region for Amazon.
entity{tuple_delimiter}Europe{tuple_delimiter}Mercado Geográfico{tuple_delimiter}Key operating region for Amazon.
entity{tuple_delimiter}Asia-Pacific{tuple_delimiter}Mercado Geográfico{tuple_delimiter}Key operating region for Amazon.
entity{tuple_delimiter}Cloud Computing{tuple_delimiter}Tendencia{tuple_delimiter}Strategic technology investment area for the company.
entity{tuple_delimiter}Artificial Intelligence{tuple_delimiter}Tendencia{tuple_delimiter}Strategic technology investment area for the company.
entity{tuple_delimiter}AWS{tuple_delimiter}Producto/Servicio{tuple_delimiter}Amazon Web Services, the company's cloud computing platform and primary profit driver.
entity{tuple_delimiter}Cloud Services Competition{tuple_delimiter}Riesgo{tuple_delimiter}Main strategic risk from increasing competition in cloud services market.
relation{tuple_delimiter}Amazon FY2023 Annual Report{tuple_delimiter}Amazon{tuple_delimiter}PERTENECE_A, documental{tuple_delimiter}The annual report presents Amazon's financial results.
relation{tuple_delimiter}Amazon FY2023 Annual Report{tuple_delimiter}FY2023{tuple_delimiter}COVERS_YEAR, temporal{tuple_delimiter}The report covers fiscal year 2023.
relation{tuple_delimiter}Amazon{tuple_delimiter}Revenue{tuple_delimiter}REPORTS_KPI, financial{tuple_delimiter}Reports total revenue of $574.8B in FY2023, up 11% year-over-year.
relation{tuple_delimiter}Amazon{tuple_delimiter}Operating Income{tuple_delimiter}REPORTS_KPI, financial{tuple_delimiter}Reports operating income of $36.9B in FY2023.
relation{tuple_delimiter}Amazon{tuple_delimiter}Cloud Computing{tuple_delimiter}INVESTS_IN, strategic{tuple_delimiter}Company continues heavy investment in cloud computing technologies.
{completion_delimiter}
""",
    """<Input Text>
```
El informe de Alimarket de 2024 sobre el Sector Cervecero en España analiza los principales actores. Mahou San Miguel lidera con una cuota de mercado del 30%. Damm, su principal competidor, le sigue con un 25%. El informe, publicado por Alimarket, destaca la tendencia de la 'Digitalización' en el canal Hostelería y el crecimiento de las cervezas 'Craft'. Ambas empresas reportan inversiones significativas en Sostenibilidad.
```

<o>
entity{tuple_delimiter}Alimarket{tuple_delimiter}Publicador{tuple_delimiter}Spanish publishing company specializing in sectoral analysis reports.
entity{tuple_delimiter}Informe Sector Cervecero España 2024{tuple_delimiter}Informe{tuple_delimiter}Sectoral analysis report on the Spanish beer industry for 2024 published by Alimarket.
entity{tuple_delimiter}2024{tuple_delimiter}Año{tuple_delimiter}Year of publication and analysis for the sectoral report.
entity{tuple_delimiter}Sector Cervecero{tuple_delimiter}Sector{tuple_delimiter}Beer industry sector analyzed in the report.
entity{tuple_delimiter}España{tuple_delimiter}Mercado Geográfico{tuple_delimiter}Geographic market analyzed in the report.
entity{tuple_delimiter}Mahou San Miguel{tuple_delimiter}Empresa{tuple_delimiter}Leading company in the Spanish beer sector.
entity{tuple_delimiter}Damm{tuple_delimiter}Empresa{tuple_delimiter}Second-largest company in the Spanish beer sector and main competitor to Mahou San Miguel.
entity{tuple_delimiter}Cuota de Mercado{tuple_delimiter}Indicador Clave{tuple_delimiter}Market share percentage representing company's portion of total market sales.
entity{tuple_delimiter}Digitalización{tuple_delimiter}Tendencia{tuple_delimiter}Digital transformation trend in the hospitality channel.
entity{tuple_delimiter}Hostelería{tuple_delimiter}Sector{tuple_delimiter}Hospitality and food service channel relevant to beer distribution.
entity{tuple_delimiter}Craft{tuple_delimiter}Categoría de Producto{tuple_delimiter}Craft beer category showing growth in the market.
entity{tuple_delimiter}Sostenibilidad{tuple_delimiter}Tendencia{tuple_delimiter}Sustainability investments by beer companies.
relation{tuple_delimiter}Informe Sector Cervecero España 2024{tuple_delimiter}Alimarket{tuple_delimiter}PUBLICADO_POR, fuente{tuple_delimiter}The report is published by Alimarket.
relation{tuple_delimiter}Informe Sector Cervecero España 2024{tuple_delimiter}2024{tuple_delimiter}CUBRE_AÑO, temporal{tuple_delimiter}The report covers the year 2024.
relation{tuple_delimiter}Informe Sector Cervecero España 2024{tuple_delimiter}Sector Cervecero{tuple_delimiter}ANALIZA_SECTOR, sectorial{tuple_delimiter}The report analyzes the beer sector.
relation{tuple_delimiter}Mahou San Miguel{tuple_delimiter}Cuota de Mercado{tuple_delimiter}REPORTA_KPI, mercado{tuple_delimiter}Reporta una cuota de mercado del 30% en el sector cervecero español.
relation{tuple_delimiter}Damm{tuple_delimiter}Cuota de Mercado{tuple_delimiter}REPORTA_KPI, mercado{tuple_delimiter}Reporta una cuota de mercado del 25% en el sector cervecero español.
{completion_delimiter}
""",
]

PROMPTS["summarize_entity_descriptions"] = """---Role---
You are a Knowledge Graph Specialist, proficient in data curation and synthesis.

---Task---
Your task is to synthesize a list of descriptions of a given entity or relation into a single, comprehensive, and cohesive summary.

---Instructions---
1. Input Format: The description list is provided in JSON format. Each JSON object (representing a single description) appears on a new line within the `Description List` section.
2. Output Format: The merged description will be returned as plain text, presented in multiple paragraphs, without any additional formatting or extraneous comments before or after the summary.
3. Comprehensiveness: The summary must integrate all key information from *every* provided description. Do not omit any important facts or details.
4. Context: Ensure the summary is written from an objective, third-person perspective; explicitly mention the name of the entity or relation for full clarity and context.
5. Context & Objectivity:
  - Write the summary from an objective, third-person perspective.
  - Explicitly mention the full name of the entity or relation at the beginning of the summary to ensure immediate clarity and context.
6. Conflict Handling:
  - In cases of conflicting or inconsistent descriptions, first determine if these conflicts arise from multiple, distinct entities or relationships that share the same name.
  - If distinct entities/relations are identified, summarize each one *separately* within the overall output.
  - If conflicts within a single entity/relation (e.g., historical discrepancies) exist, attempt to reconcile them or present both viewpoints with noted uncertainty.
7. Length Constraint: The summary's total length must not exceed {summary_length} tokens, while still maintaining depth and completeness.
8. Language: The entire output must be written in {language}. Proper nouns (e.g., personal names, place names, organization names) should be retained in their original language if a proper, widely accepted translation is not available or would cause ambiguity.

---Input---
{description_type} Name: {description_name}

Description List:

{description_list}


---Output---
"""

PROMPTS["fail_response"] = (
    "Sorry, I'm not able to provide an answer to that question.[no-context]"
)

PROMPTS["rag_response"] = """---Role---

You are an expert AI assistant specializing in synthesizing information from a provided knowledge base. Your primary function is to answer user queries accurately by ONLY using the information within the provided **Context**.

---Goal---

Generate a comprehensive, well-structured answer to the user query.
The answer must integrate relevant facts from the Knowledge Graph and Document Chunks found in the **Context**.
Consider the conversation history if provided to maintain conversational flow and avoid repeating information.

---Instructions---

1. Step-by-Step Instruction:
  - Carefully determine the user's query intent in the context of the conversation history to fully understand the user's information need.
  - Scrutinize both `Knowledge Graph Data` and `Document Chunks` in the **Context**. Identify and extract all pieces of information that are directly relevant to answering the user query.
  - Weave the extracted facts into a coherent and logical response. Your own knowledge must ONLY be used to formulate fluent sentences and connect ideas, NOT to introduce any external information.
  - Track the reference_id of the document chunk which directly support the facts presented in the response. Correlate reference_id with the entries in the `Reference Document List` to generate the appropriate citations.
  - Generate a references section at the end of the response. Each reference document must directly support the facts presented in the response.
  - Do not generate anything after the reference section.

2. Content & Grounding:
  - Strictly adhere to the provided context from the **Context**; DO NOT invent, assume, or infer any information not explicitly stated.
  - If the answer cannot be found in the **Context**, state that you do not have enough information to answer. Do not attempt to guess.

3. Formatting & Language:
  - The response MUST be in the same language as the user query.
  - The response MUST utilize Markdown formatting for enhanced clarity and structure (e.g., headings, bold text, bullet points).
  - The response should be presented in {response_type}.

4. References Section Format:
  - The References section should be under heading: `### References`
  - Reference list entries should adhere to the format: `* [n] Document Title`. Do not include a caret (`^`) after opening square bracket (`[`).
  - The Document Title in the citation must retain its original language.
  - Output each citation on an individual line
  - Provide maximum of 5 most relevant citations.
  - Do not generate footnotes section or any comment, summary, or explanation after the references.

5. Reference Section Example:
```
### References

- [1] Document Title One
- [2] Document Title Two
- [3] Document Title Three
```

6. Additional Instructions: {user_prompt}


---Context---

{context_data}
"""

PROMPTS["naive_rag_response"] = """---Role---

You are an expert AI assistant specializing in synthesizing information from a provided knowledge base. Your primary function is to answer user queries accurately by ONLY using the information within the provided **Context**.

---Goal---

Generate a comprehensive, well-structured answer to the user query.
The answer must integrate relevant facts from the Document Chunks found in the **Context**.
Consider the conversation history if provided to maintain conversational flow and avoid repeating information.

---Instructions---

1. Step-by-Step Instruction:
  - Carefully determine the user's query intent in the context of the conversation history to fully understand the user's information need.
  - Scrutinize `Document Chunks` in the **Context**. Identify and extract all pieces of information that are directly relevant to answering the user query.
  - Weave the extracted facts into a coherent and logical response. Your own knowledge must ONLY be used to formulate fluent sentences and connect ideas, NOT to introduce any external information.
  - Track the reference_id of the document chunk which directly support the facts presented in the response. Correlate reference_id with the entries in the `Reference Document List` to generate the appropriate citations.
  - Generate a **References** section at the end of the response. Each reference document must directly support the facts presented in the response.
  - Do not generate anything after the reference section.

2. Content & Grounding:
  - Strictly adhere to the provided context from the **Context**; DO NOT invent, assume, or infer any information not explicitly stated.
  - If the answer cannot be found in the **Context**, state that you do not have enough information to answer. Do not attempt to guess.

3. Formatting & Language:
  - The response MUST be in the same language as the user query.
  - The response MUST utilize Markdown formatting for enhanced clarity and structure (e.g., headings, bold text, bullet points).
  - The response should be presented in {response_type}.

4. References Section Format:
  - The References section should be under heading: `### References`
  - Reference list entries should adhere to the format: `* [n] Document Title`. Do not include a caret (`^`) after opening square bracket (`[`).
  - The Document Title in the citation must retain its original language.
  - Output each citation on an individual line
  - Provide maximum of 5 most relevant citations.
  - Do not generate footnotes section or any comment, summary, or explanation after the references.

5. Reference Section Example:
```
### References

- [1] Document Title One
- [2] Document Title Two
- [3] Document Title Three
```

6. Additional Instructions: {user_prompt}


---Context---

{content_data}
"""

PROMPTS["kg_query_context"] = """
Knowledge Graph Data (Entity):
```json
{entities_str}
```

Knowledge Graph Data (Relationship):
```json
{relations_str}
```

Document Chunks (Each entry has a reference_id refer to the `Reference Document List`):
```json
{text_chunks_str}
```

Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):
```
{reference_list_str}
```

"""

PROMPTS["naive_query_context"] = """
Document Chunks (Each entry has a reference_id refer to the `Reference Document List`):
```json
{text_chunks_str}
```

Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):
```
{reference_list_str}
```

"""

PROMPTS["keywords_extraction"] = """---Role---
You are an expert keyword extractor, specializing in analyzing user queries for a Retrieval-Augmented Generation (RAG) system. Your purpose is to identify both high-level and low-level keywords in the user's query that will be used for effective document retrieval.

---Goal---
Given a user query, your task is to extract two distinct types of keywords:
1. **high_level_keywords**: for overarching concepts or themes, capturing user's core intent, the subject area, or the type of question being asked.
2. **low_level_keywords**: for specific entities or details, identifying the specific entities, proper nouns, technical jargon, product names, or concrete items.

---Instructions & Constraints---
1. **Output Format**: Your output MUST be a valid JSON object and nothing else. Do not include any explanatory text, markdown code fences (like ```json), or any other text before or after the JSON. It will be parsed directly by a JSON parser.
2. **Source of Truth**: All keywords must be explicitly derived from the user query, with both high-level and low-level keyword categories are required to contain content.
3. **Concise & Meaningful**: Keywords should be concise words or meaningful phrases. Prioritize multi-word phrases when they represent a single concept. For example, from "latest financial report of Apple Inc.", you should extract "latest financial report" and "Apple Inc." rather than "latest", "financial", "report", and "Apple".
4. **Handle Edge Cases**: For queries that are too simple, vague, or nonsensical (e.g., "hello", "ok", "asdfghjkl"), you must return a JSON object with empty lists for both keyword types.

---Examples---
{examples}

---Real Data---
User Query: {query}

---Output---
Output:"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "How does international trade influence global economic stability?"

Output:
{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}

""",
    """Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"

Output:
{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}

""",
    """Example 3:

Query: "What is the role of education in reducing poverty?"

Output:
{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}

""",
]