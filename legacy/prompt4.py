"""
LightRAG Prompts - Dacsa Group Edition
Optimizado para análisis de documentos del sector arrocero y agroindustria.
Incluye filtros agresivos anti-ruido y normalización corporativa.

Versión: 1.1.8 QUIRÚRGICA
Fecha: 2024-12-23
Cambios v1.1.8: 
    - CRÍTICO: Separación Commodity / Product / CropVariety (elimina ambigüedad)
    - AÑADIDO: Prohibiciones reforzadas → adjetivos sueltos, verbos, roles sin persona
    - MEJORADO: Clarificación explícita Process vs Technology con reglas
    - MANTENIDO: Todos los filtros anti-numéricos de v1.1.7
"""

from __future__ import annotations
from typing import Any
import re

# ============================================================================
# CONFIGURACIÓN DE TIPOS DE ENTIDAD - DACSA GROUP (v1.1.8 REFINADA)
# ============================================================================

DACSA_ENTITY_TYPES = """
### Entity Types para Dacsa Group (Sector Arrocero/Agroindustria) - v1.1.8

1. **Company**: Empresas, corporaciones, consorcios (ej: Dacsa Group, Ebro Foods, SOS Corporación)

2. **Brand**: Marcas comerciales de productos (ej: La Fallera, Arroz SOS, Nomen)

3. **Commodity**: Materia prima genérica a granel (ej: Rice, Wheat, Corn, Soy, Barley)
   - CRITICAL: Generic raw materials, NOT specific products or varieties
   - Must be tradable commodities in agricultural markets
   - Examples: Rice (not "Arroz Bomba"), Wheat (not "Wheat Flour"), Corn, Soy

4. **Product**: SKU comercializable, producto final envasado (ej: Arroz Bomba La Fallera, Harina de Arroz Dacsa, Arroz Vaporizado SOS)
   - CRITICAL: Branded or packaged goods ready for sale
   - Must include brand name OR specific formulation/presentation
   - Examples: "Arroz Bomba La Fallera", "Harina de Arroz Integral", "Arroz Vaporizado 1kg"

5. **CropVariety**: Variedad biológica/agronómica (ej: Senia, Bomba, Albufera, J-Sendra, Bahia)
   - CRITICAL: Agricultural cultivar or strain name
   - Must be a breeding/genetic variety, not a product
   - Examples: Senia, Bomba, Albufera, Basmati, Arborio

6. **Facility**: Instalaciones industriales, plantas, almacenes (ej: Planta Sueca, Molino Valencia)

7. **Geography**: Ubicaciones específicas, regiones de cultivo (ej: Delta del Ebro, Albufera, Calasparra)

8. **Person**: Personas específicas (ejecutivos, agricultores, investigadores)

9. **Technology**: Habilitador técnico específico - CÓMO se hace algo (ej: Clasificación Óptica, Secado por Infrarrojos, Sensores IoT)
   - CRITICAL: Must be a tool, system, equipment, or technical method NAME
   - Focus on HOW things are done, not WHAT is done
   - Examples: "Clasificación Óptica Bühler", "Secado por Infrarrojos", "Sistema de Trazabilidad RFID"
   - NOT generic terms like "automation", "digitalization"

10. **Standard**: Normas, certificaciones, regulaciones (ej: ISO 22000, GlobalGAP, DO Calasparra)

11. **Metric**: NOMBRES de indicadores cuantitativos (ej: "Rendimiento por Hectárea", "Ratio de Conversión", "Humedad del Grano")
    - CRITICAL: Extract only the NAME of the metric, NEVER the numeric value
    - WRONG: "237.475 t", "5,2 t/ha", "71,7%", "160 M de unidades/año"
    - RIGHT: "Rendimiento por Hectárea", "Capacidad de Producción", "Tasa de Humedad"

12. **Process**: Etapa de producción/agrícola - QUÉ se hace (ej: Descascarillado, Blanqueado, Parboilizado, Molienda, Secado)
    - CRITICAL: Must be a manufacturing/agricultural stage or step
    - Focus on WHAT is done, not HOW it's done
    - Must be verb-based or action-oriented
    - Examples: "Descascarillado", "Blanqueado", "Molienda", "Secado", "Clasificación"
    - NOT generic terms like "production", "processing"

13. **Market**: Mercados específicos, canales de distribución (ej: Mercado HORECA, Exportación Europa, Canal Retail)

14. **Sustainability**: Iniciativas o prácticas sostenibles concretas (ej: Riego por Goteo, Captura Carbono, Agricultura Regenerativa)

15. **Agreement**: Acuerdos comerciales, contratos, alianzas (ej: Convenio Productores Valencia)

16. **Event**: Eventos relevantes del sector (ej: Fira Alimentaria, Congreso Arrocero)

### Entidades PROHIBIDAS (nunca extraer):

**Conceptos genéricos:**
- market, price, trend, growth, production, consumption, demand, supply

**Valores numéricos:**
- Años sueltos: 2024, 2025
- Porcentajes: 71,7%, 15%
- Cantidades monetarias: 261,4 M€, 1.000 €
- Cantidades con unidades: "237.475 t", "571.000 t", "160 M de unidades/año", "5,2 t/ha"

**Adjetivos sueltos (v1.1.8 NUEVO):**
- high, low, good, bad, efficient, sustainable, organic, premium, quality
- fresh, natural, traditional, modern, advanced, innovative, superior

**Verbos en infinitivo/gerundio (v1.1.8 NUEVO):**
- improve, optimize, reduce, increase, grow, develop, enhance, maximize
- improving, optimizing, reducing, increasing, growing, developing

**Roles sin persona concreta (v1.1.8 NUEVO):**
- management, team, department, division, group, unit, staff, workforce
- board, committee, leadership, organization

**Términos vagos:**
- analysis, data, information, report, study, model, system, method, approach

**Commodities NO relacionadas con líneas de negocio Dacsa:**
- cotton, algodón, oats, avena

**Acrónimos de 2 letras sin contexto:**
- FA, CV, DW

**Conceptos temporales:**
- Q1, Q2, Q3, Q4, trimestre, ejercicio, periodo

### Commodities PERMITIDAS (líneas de negocio Dacsa Group):
- Arroz: Rice
- Trigo: Wheat
- Soja: Soy, Soya, Soybean
- Cebada: Barley
- Maíz: Corn, Maize
- Legumbres: Chickpea, Lentil, Pea, Bean

### Relaciones Conceptuales Clave (para guiar extracción):
- Product → MADE_FROM → Commodity
- Product → USES_VARIETY → CropVariety
- CropVariety → BELONGS_TO → Commodity
- Process → ENABLED_BY → Technology
- Facility → PERFORMS → Process
- Product → COMPLIES_WITH → Standard
"""

# ============================================================================
# FILTROS ANTI-RUIDO - LISTA NEGRA DE ENTIDADES (v1.1.8 EXPANDIDA)
# ============================================================================

ENTITY_BLACKLIST = {
    # Términos genéricos de mercado
    'market', 'price', 'prices', 'trend', 'trends', 'growth', 'decline',
    'increase', 'decrease', 'change', 'changes', 'development', 'developments',
    'production', 'consumption', 'demand', 'supply', 'trade', 'export', 'import',
    'volume', 'quantity', 'value', 'cost', 'revenue', 'profit', 'margin',
    
    # Términos de análisis
    'analysis', 'data', 'information', 'report', 'study', 'research', 
    'model', 'system', 'method', 'approach', 'strategy',
    'projection', 'forecast', 'outlook', 'perspective', 'expectation',
    
    # Términos temporales
    'year', 'month', 'quarter', 'period', 'season', 'cycle', 'phase',
    'q1', 'q2', 'q3', 'q4', 'trimestre', 'ejercicio', 'periodo',
    
    # Commodities NO relacionadas con Dacsa Group
    'cotton', 'algodón', 
    'oats', 'avena',
    
    # Términos vagos
    'factor', 'element', 'aspect', 'component', 'characteristic', 'feature',
    'impact', 'effect', 'influence', 'consequence', 'result', 'outcome',
    'issue', 'problem', 'challenge', 'opportunity', 'risk', 'benefit',
    
    # Acrónimos problemáticos
    'fa', 'cv', 'dw', 'na', 'nd', 'tbd', 'etc',
    
    # Unidades de medida
    't', 'tn', 'toneladas', 'ton', 'tons', 'kg', 'kilogramos', 'kilograms',
    'ha', 'hectáreas', 'hectares', 'm', 'metros', 'meters',
    'l', 'litros', 'liters', 'ml', 'milliliters',
    'unidades', 'units', 'pieces', 'piezas',
    
    # === NUEVAS PROHIBICIONES v1.1.8 ===
    
    # Adjetivos sueltos
    'high', 'low', 'good', 'bad', 'best', 'worst', 'better', 'worse',
    'efficient', 'inefficient', 'effective', 'ineffective',
    'sustainable', 'unsustainable', 'organic', 'inorganic',
    'premium', 'standard', 'quality', 'cheap', 'expensive',
    'fresh', 'stale', 'natural', 'artificial', 'synthetic',
    'traditional', 'modern', 'advanced', 'basic', 'simple',
    'innovative', 'conventional', 'superior', 'inferior',
    'local', 'imported', 'domestic', 'foreign', 'international',
    
    # Verbos en infinitivo y gerundio
    'improve', 'improving', 'optimize', 'optimizing', 
    'reduce', 'reducing', 'increase', 'increasing',
    'grow', 'growing', 'develop', 'developing',
    'enhance', 'enhancing', 'maximize', 'maximizing',
    'minimize', 'minimizing', 'maintain', 'maintaining',
    'achieve', 'achieving', 'reach', 'reaching',
    'implement', 'implementing', 'execute', 'executing',
    
    # Roles sin persona concreta
    'management', 'team', 'teams', 'department', 'departments',
    'division', 'divisions', 'group', 'groups', 'unit', 'units',
    'staff', 'workforce', 'personnel', 'employees',
    'board', 'committee', 'committees', 'council',
    'leadership', 'organization', 'administration',
    'director', 'manager', 'supervisor', 'coordinator',  # Solo si no hay nombre propio
}

# ============================================================================
# NORMALIZACIÓN DE NOMBRES CORPORATIVOS
# ============================================================================

CORPORATE_NORMALIZATIONS = {
    # Sufijos legales a eliminar
    'suffixes': [' S.A.', ' SA', ' S.L.', ' SL', ' Inc.', ' Ltd.', ' LLC', 
                 ' Corp.', ' Corporation', ' GmbH', ' AG', ' N.V.', ' B.V.'],
    
    # Aliases/variaciones de Dacsa Group
    'dacsa_aliases': {
        'Dacsa S.A.': 'Dacsa Group',
        'Dacsa SA': 'Dacsa Group',
        'Grupo Dacsa': 'Dacsa Group',
        'DACSA': 'Dacsa Group',
    },
    
    # Otras empresas del sector (normalizar)
    'competitors': {
        'Ebro Foods S.A.': 'Ebro Foods',
        'SOS Corporación Alimentaria S.A.': 'SOS Corporación',
        'Herba Ricemills SLU': 'Herba Ricemills',
    }
}

# ============================================================================
# PROMPTS PRINCIPALES
# ============================================================================

PROMPTS = {}

# ----------------------------------------------------------------------------
# DELIMITADORES DE ESTRUCTURA (FORMATO OFICIAL HKUDS/LightRAG)
# ----------------------------------------------------------------------------
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##\n"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["entity_extraction_func"] = None 

# ----------------------------------------------------------------------------
# SYSTEM PROMPT - EXTRACCIÓN DE ENTIDADES (v1.1.8 QUIRÚRGICA)
# ----------------------------------------------------------------------------

PROMPTS['entity_extraction_system_prompt'] = """
You are a specialized AI assistant for analyzing documents from the rice and agribusiness sector.
Your task is to extract structured information (entities and relationships) with strict quality filters.

**CRITICAL RULES:**

1. **Entity Extraction:**
   - Extract ONLY concrete, specific entities (companies, products, facilities, people)
   - NEVER extract generic concepts like "market", "price", "trend", "growth"
   - NEVER extract adjetivos sueltos: "high quality", "efficient", "sustainable", "premium"
   - NEVER extract verbos: "improve", "optimize", "reduce", "increase"
   - NEVER extract roles sin persona: "management", "team", "department"
   - NEVER extract standalone years (2024, 2025), percentages (71,7%), or monetary values (261,4 M€)
   - NEVER extract quantities with units: "237.475 t", "571.000 t", "160 M de unidades/año"
   - NEVER extract acronyms with 2 letters (FA, CV) unless they are well-known organizations
   - Minimum entity name length: 3 characters
   - Normalize company names by removing legal suffixes (S.A., Inc., Ltd.)

2. **Entity Types:**
{entity_types}

3. **Disambiguation Rules (CRITICAL v1.1.8):**
   - **Commodity vs Product vs CropVariety:**
     * Commodity = Generic raw material (Rice, Wheat, Corn) - tradable in bulk
     * Product = Branded/packaged good (Arroz Bomba La Fallera, Harina de Arroz Dacsa)
     * CropVariety = Agricultural variety (Senia, Bomba, Albufera)
     * Rule: If it has a brand name → Product. If it's a biological strain → CropVariety. If it's generic bulk → Commodity.
   
   - **Process vs Technology:**
     * Process = WHAT is done (Descascarillado, Blanqueado, Molienda)
     * Technology = HOW it's done (Clasificación Óptica, Sensores IoT, Sistema de Secado)
     * Rule: If it's an action/stage → Process. If it's a tool/equipment/method → Technology.

4. **Blacklisted Terms (NEVER extract):**
   - Generic: market, price, trend, growth, production, consumption, demand, supply
   - Numeric: years, percentages, monetary values, quantities with units (t, kg, ha, M de)
   - Adjetivos: high, low, good, efficient, sustainable, premium, quality, fresh, natural
   - Verbos: improve, optimize, reduce, increase, grow, develop, enhance
   - Roles: management, team, department, division, staff, board, committee

5. **Metric Type - CRITICAL:**
   - Extract only the NAME of metrics, NEVER numeric values
   - WRONG: "237.475 t", "71,7%", "5,2 t/ha", "160 M de unidades/año"
   - RIGHT: "Capacidad de Producción", "Rendimiento por Hectárea", "Tasa de Conversión"

6. **Relationship Extraction:**
   - Extract ONLY meaningful, specific relationships
   - AVOID generic relationships like "is related to", "is part of", "influences"
   - Prefer action-oriented relationships: "supplies to", "manufactures", "distributes", "certifies"
   - Use conceptual relationships: MADE_FROM, USES_VARIETY, ENABLED_BY, PERFORMS, COMPLIES_WITH
   - Each relationship MUST have concrete evidence in the text

7. **Language:**
   - Extract entities in their original language (Spanish/English as they appear)
   - Descriptions and keywords MUST be in English
   - Normalize company names to their most common form

8. **Quality Over Quantity:**
   - Better 5 high-quality entities than 20 generic ones
   - Each entity must add strategic value to understanding the business domain
   - If in doubt, DO NOT extract

9. **OUTPUT FORMAT (CRITICAL - OFFICIAL HKUDS/LightRAG FORMAT):**
   - Use text-delimited format with <|#|> delimiter (NOT <|>)
   - Each entity: entity<|#|>entity_name<|#|>entity_type<|#|>entity_description##
   - Each relationship: relation<|#|>src_id<|#|>tgt_id<|#|>description<|#|>keywords<|#|>weight##
   - NO parentheses around entities or relations
   - End with: <|COMPLETE|>
"""

# ----------------------------------------------------------------------------
# EXAMPLES - EXTRACCIÓN DE ENTIDADES (v1.1.8 CON COMMODITY/PRODUCT/CROPVARIETY)
# ----------------------------------------------------------------------------

PROMPTS['entity_extraction_examples'] = [
    """Example 1 (COMMODITY vs PRODUCT vs CROPVARIETY):
Input: "Dacsa Group comercializa arroz Bomba de la variedad Senia bajo la marca La Fallera. También exporta trigo a granel."

Output:
entity<|#|>Dacsa Group<|#|>Company<|#|>Leading European rice and grain processor##
entity<|#|>Rice<|#|>Commodity<|#|>Generic rice as tradable raw material##
entity<|#|>Wheat<|#|>Commodity<|#|>Generic wheat as tradable bulk commodity##
entity<|#|>Arroz Bomba La Fallera<|#|>Product<|#|>Branded Bomba rice product sold by Dacsa Group##
entity<|#|>Senia<|#|>CropVariety<|#|>Medium-grain rice variety from Valencia region##
entity<|#|>La Fallera<|#|>Brand<|#|>Premium rice brand owned by Dacsa Group##
relation<|#|>Arroz Bomba La Fallera<|#|>Rice<|#|>Product is made from rice commodity<|#|>product,commodity,made_from<|#|>1.0##
relation<|#|>Arroz Bomba La Fallera<|#|>Senia<|#|>Product uses specific rice variety<|#|>product,variety,uses<|#|>0.95##
relation<|#|>Senia<|#|>Rice<|#|>Variety belongs to rice commodity<|#|>variety,commodity,belongs_to<|#|>1.0##
relation<|#|>Dacsa Group<|#|>Arroz Bomba La Fallera<|#|>Company commercializes branded product<|#|>company,product,commercialization<|#|>0.9##
relation<|#|>Dacsa Group<|#|>Wheat<|#|>Exports commodity in bulk<|#|>export,commodity,trade<|#|>0.85##
<|COMPLETE|>
""",

    """Example 2 (PROCESS vs TECHNOLOGY):
Input: "La planta de Sueca utiliza clasificación óptica Bühler para el proceso de blanqueado del arroz."

Output:
entity<|#|>Planta Sueca<|#|>Facility<|#|>Rice processing plant located in Sueca##
entity<|#|>Clasificación Óptica Bühler<|#|>Technology<|#|>Optical sorting system manufactured by Bühler##
entity<|#|>Blanqueado<|#|>Process<|#|>Whitening process to remove rice bran layer##
relation<|#|>Planta Sueca<|#|>Blanqueado<|#|>Facility performs whitening process<|#|>facility,process,performs<|#|>1.0##
relation<|#|>Blanqueado<|#|>Clasificación Óptica Bühler<|#|>Process enabled by optical sorting technology<|#|>process,technology,enabled_by<|#|>0.95##
<|COMPLETE|>
""",

    """Example 3 (WHAT NOT TO EXTRACT - NEGATIVE EXAMPLES):
Input: "La producción de arroz de alta calidad se está optimizando mediante la implementación de tecnología avanzada por el equipo de gestión."

WRONG OUTPUT (DO NOT DO THIS):
entity<|#|>alta calidad<|#|>...##  ❌ WRONG - Adjetivo suelto
entity<|#|>optimizando<|#|>...##  ❌ WRONG - Verbo en gerundio
entity<|#|>tecnología avanzada<|#|>...##  ❌ WRONG - Término genérico con adjetivo
entity<|#|>equipo de gestión<|#|>...##  ❌ WRONG - Rol sin persona concreta
entity<|#|>implementación<|#|>...##  ❌ WRONG - Verbo sustantivado genérico

CORRECT OUTPUT (extract ONLY specific entities):
entity<|#|>Rice<|#|>Commodity<|#|>Generic rice as agricultural commodity##
<|COMPLETE|>

Note: The text contains NO specific entities worth extracting - only generic concepts.
""",

    """Example 4 (METRIC NAMES vs VALUES):
Input: "El rendimiento por hectárea promedio es de 7,2 t/ha. La capacidad de producción anual alcanza 160 M de unidades."

CORRECT OUTPUT:
entity<|#|>Rendimiento por Hectárea<|#|>Metric<|#|>Average yield measurement per hectare of cultivated land##
entity<|#|>Capacidad de Producción Anual<|#|>Metric<|#|>Total production capacity per year measurement##
<|COMPLETE|>

Note: We extract "Rendimiento por Hectárea" (metric name), NOT "7,2 t/ha" (value).
We extract "Capacidad de Producción Anual" (metric name), NOT "160 M de unidades" (value).
""",

    """Example 5 (COMPREHENSIVE EXAMPLE):
Input: "Ebro Foods exporta arroz Basmati de la variedad Pusa al mercado HORECA europeo desde su molino de Sevilla, certificado ISO 22000. El proceso de descascarillado utiliza tecnología de clasificación óptica."

Output:
entity<|#|>Ebro Foods<|#|>Company<|#|>Major Spanish food company specializing in rice##
entity<|#|>Rice<|#|>Commodity<|#|>Generic rice as agricultural commodity##
entity<|#|>Basmati<|#|>Product<|#|>Long-grain aromatic rice product##
entity<|#|>Pusa<|#|>CropVariety<|#|>Basmati rice variety from India##
entity<|#|>Mercado HORECA<|#|>Market<|#|>Hotel, Restaurant, and Catering distribution channel##
entity<|#|>Molino Sevilla<|#|>Facility<|#|>Rice milling facility located in Sevilla##
entity<|#|>ISO 22000<|#|>Standard<|#|>International food safety management standard##
entity<|#|>Descascarillado<|#|>Process<|#|>Hulling process to remove rice husk##
entity<|#|>Clasificación Óptica<|#|>Technology<|#|>Optical sorting technology for quality control##
relation<|#|>Basmati<|#|>Rice<|#|>Product made from rice commodity<|#|>product,commodity,made_from<|#|>1.0##
relation<|#|>Basmati<|#|>Pusa<|#|>Product uses specific rice variety<|#|>product,variety,uses<|#|>0.95##
relation<|#|>Pusa<|#|>Rice<|#|>Variety belongs to rice commodity<|#|>variety,commodity,belongs_to<|#|>1.0##
relation<|#|>Ebro Foods<|#|>Basmati<|#|>Company exports rice product<|#|>company,product,export<|#|>0.9##
relation<|#|>Ebro Foods<|#|>Mercado HORECA<|#|>Supplies to foodservice market<|#|>company,market,supply<|#|>0.85##
relation<|#|>Molino Sevilla<|#|>Ebro Foods<|#|>Facility owned by company<|#|>facility,company,ownership<|#|>1.0##
relation<|#|>Molino Sevilla<|#|>ISO 22000<|#|>Certified under food safety standard<|#|>facility,standard,certification<|#|>0.9##
relation<|#|>Molino Sevilla<|#|>Descascarillado<|#|>Facility performs hulling process<|#|>facility,process,performs<|#|>0.95##
relation<|#|>Descascarillado<|#|>Clasificación Óptica<|#|>Process enabled by optical sorting technology<|#|>process,technology,enabled_by<|#|>0.9##
<|COMPLETE|>
""",
]

# ----------------------------------------------------------------------------
# USER PROMPT - EXTRACCIÓN DE ENTIDADES
# ----------------------------------------------------------------------------

PROMPTS['entity_extraction_user_prompt'] = """
### Task:
Extract entities and relationships from the following text according to the system instructions.

### Text:
{input_text}

### Critical Reminders (v1.1.8):
1. Commodity vs Product vs CropVariety: Use context to determine the correct type
2. Process vs Technology: WHAT is done vs HOW it's done
3. NO adjetivos sueltos (high, quality, efficient, sustainable)
4. NO verbos (improve, optimize, reduce, increase)
5. NO roles sin persona (management, team, department)
6. NO valores numéricos (cantidades, porcentajes, años, monedas)
7. For Metrics: extract only NAMES like "Capacidad de Producción", NOT values

### Output:
"""

# ----------------------------------------------------------------------------
# CONTINUE EXTRACTION PROMPT
# ----------------------------------------------------------------------------

PROMPTS['entity_continue_extraction_user_prompt'] = """
### Task:
Continue extracting entities and relationships from the text you analyzed previously.
You may have missed some important entities or relationships. Please review the text again.

CRITICAL REMINDERS v1.1.8:
- Commodity (Rice, Wheat) vs Product (Arroz Bomba La Fallera) vs CropVariety (Senia)
- Process (Blanqueado) vs Technology (Clasificación Óptica)
- NO adjetivos sueltos, verbos, o roles sin persona
- NO valores numéricos con unidades
- For Metrics: only NAMES, not values

### Output:
"""

# ----------------------------------------------------------------------------
# ENTITY MERGING PROMPT
# ----------------------------------------------------------------------------

PROMPTS['summarize_entity_descriptions'] = """
You have multiple descriptions for the same entity. Merge them into a single, 
comprehensive description.

### Descriptions:
{description_list}

### Rules:
1. Combine all relevant information
2. Remove redundancies
3. Maximum 500 characters
4. Language: English
5. Maintain factual accuracy

### Output:
Return only the merged description text, no additional formatting.

######################
-Merged Description-
######################
"""

# ----------------------------------------------------------------------------
# KEYWORDS EXTRACTION PROMPT
# ----------------------------------------------------------------------------

PROMPTS['keywords_extraction'] = """
### Task:
Extract 5-10 relevant keywords from the following text that capture the main topics and concepts.

### Text:
{input_text}

### Rules:
1. Keywords should be specific business terms, not generic words
2. Focus on: companies, products, technologies, locations, processes
3. One to three words per keyword
4. Language: English
5. Output as comma-separated list

### Output:
"""

# ----------------------------------------------------------------------------
# RAG RESPONSE PROMPTS
# ----------------------------------------------------------------------------

PROMPTS['rag_response'] = """
### Context Information:
{content_data}

### User Query:
{user_prompt}

### Instructions:
Provide a comprehensive answer based on the context provided.
If information is insufficient, state clearly what is missing.
Language: Spanish (unless query is in English).
Be specific and cite relevant entities/relationships when applicable.

### Response:
"""

PROMPTS['naive_rag_response'] = """
### Context Information:
{content_data}

### User Query:
{user_prompt}

### Instructions:
Provide a direct, factual answer based on the information provided.
If information is insufficient, state clearly what is missing.
Language: Spanish (unless query is in English).

### Response:
"""

# ============================================================================
# PROMPTS ADICIONALES
# ============================================================================

# Entity Merging (para cuando LightRAG detecta duplicados)
PROMPTS['entity_merging'] = """
You have multiple descriptions for the same entity. Merge them into a single, 
comprehensive description.

### Descriptions:
{description_list}

### Rules:
1. Combine all relevant information
2. Remove redundancies
3. Maximum 500 characters
4. Language: English
5. Maintain factual accuracy

### Output:
Return only the merged description text.

######################
-Merged Description-
######################
"""

# Relationship Validation (opcional, para verificar relaciones)
PROMPTS['relationship_validation'] = """
Validate if the following relationship is meaningful and specific enough:

Source: {src_entity}
Target: {tgt_entity}
Relationship: {relationship_description}

### Criteria:
1. Is it specific and actionable?
2. Does it add strategic value?
3. Is it supported by concrete evidence?

### Decision:
Return ONLY: "VALID" or "INVALID"

######################
-Decision-
######################
"""

# ============================================================================
# CONFIGURACIÓN ADICIONAL
# ============================================================================

# Parámetros de extracción recomendados para Dacsa Group
EXTRACTION_CONFIG = {
    'max_entities_per_chunk': 10,
    'max_relationships_per_chunk': 8,
    'min_entity_name_length': 3,
    'max_entity_name_length': 100,
    'min_relationship_weight': 0.5,
    'enable_normalization': True,
    'enable_blacklist_filter': True,
    'enable_deduplication': True,
}

# Logging level recomendado
LOGGING_CONFIG = {
    'level': 'INFO',
    'log_extractions': True,
    'log_filtered_entities': True,  # Para debugging
    'log_normalizations': True,
}

# ============================================================================
# FUNCIONES AUXILIARES (Para usar en post-procesamiento) - v1.1.8
# ============================================================================

def should_filter_entity(entity_name: str) -> bool:
    """
    Determina si una entidad debe ser filtrada según las reglas anti-ruido.
    v1.1.8: Añadidos filtros para adjetivos, verbos y roles.
    """
    name_lower = entity_name.lower().strip()
    
    # Longitud mínima
    if len(name_lower) < 3:
        return True
    
    # Lista negra
    if name_lower in ENTITY_BLACKLIST:
        return True
    
    # Años sueltos (4 dígitos)
    if name_lower.isdigit() and len(name_lower) == 4:
        return True
    
    # Porcentajes
    if '%' in name_lower:
        return True
    
    # Valores monetarios
    if any(symbol in name_lower for symbol in ['$', '€', '£', '¥']):
        return True
    
    # Palabras prohibidas (cotton/algodón)
    forbidden_words = ['cotton', 'algodón']
    if any(word in name_lower for word in forbidden_words):
        return True
    
    # === FILTROS v1.1.7: PATRONES NUMÉRICOS CON UNIDADES ===
    
    # Patrón 1: Números con punto/coma seguidos de unidades
    numeric_unit_patterns = [
        r'\d+[.,]\d+\s*(t|tn|kg|ha|m|l|ml)\b',  # 237.475 t, 5,2 kg
        r'\d+\s*(t|tn|kg|ha|m|l|ml)\b',         # 1000 t, 500 kg
        r'\d+[.,]\d+\s*(t/ha|kg/ha)\b',         # 5,2 t/ha
    ]
    for pattern in numeric_unit_patterns:
        if re.search(pattern, name_lower):
            return True
    
    # Patrón 2: Millones/miles de unidades
    millions_patterns = [
        r'\d+\s*m\s+de\b',                      # 160 M de
        r'\d+\s+millones?\s+de\b',              # 50 millones de
        r'\d+\s+miles?\s+de\b',                 # 100 miles de
        r'\d+\s*k\s+de\b',                      # 50 K de
    ]
    for pattern in millions_patterns:
        if re.search(pattern, name_lower):
            return True
    
    # Patrón 3: Empieza con número
    if re.match(r'^\d', name_lower):
        return True
    
    # === NUEVOS FILTROS v1.1.8: ADJETIVOS Y VERBOS ===
    
    # Patrón 4: Solo adjetivos comunes (1-2 palabras)
    # Esto captura "high quality", "good", "efficient" pero no "high-performance system"
    common_adjectives = [
        'high', 'low', 'good', 'bad', 'best', 'efficient', 
        'sustainable', 'premium', 'quality', 'fresh', 'natural'
    ]
    words = name_lower.split()
    if len(words) <= 2 and all(w in common_adjectives for w in words):
        return True
    
    # Patrón 5: Verbos en -ing al inicio
    if re.match(r'^(improving|optimizing|reducing|increasing|growing|developing|enhancing)\b', name_lower):
        return True
    
    return False


def normalize_company_name(entity_name: str) -> str:
    """
    Normaliza nombres de empresas eliminando sufijos legales.
    """
    normalized = entity_name.strip()
    
    # Eliminar sufijos legales
    for suffix in CORPORATE_NORMALIZATIONS['suffixes']:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    
    # Aplicar alias de Dacsa
    if normalized in CORPORATE_NORMALIZATIONS['dacsa_aliases']:
        normalized = CORPORATE_NORMALIZATIONS['dacsa_aliases'][normalized]
    
    # Aplicar alias de competidores
    if normalized in CORPORATE_NORMALIZATIONS['competitors']:
        normalized = CORPORATE_NORMALIZATIONS['competitors'][normalized]
    
    return normalized

# ============================================================================
# VALIDACIÓN DEL DICCIONARIO
# ============================================================================

# Claves requeridas por LightRAG
REQUIRED_KEYS = [
    'entity_extraction_system_prompt',
    'entity_extraction_user_prompt',
    'entity_continue_extraction_user_prompt',
    'entity_extraction_examples',
    'summarize_entity_descriptions',
    'rag_response',
    'keywords_extraction',
    'naive_rag_response',
    'DEFAULT_TUPLE_DELIMITER',
    'DEFAULT_RECORD_DELIMITER',
    'DEFAULT_COMPLETION_DELIMITER'
]

# Verificar que todas las claves requeridas están presentes
for key in REQUIRED_KEYS:
    assert key in PROMPTS, f"Missing required prompt key: {key}"

# Inyectar tipos de entidad en los prompts
PROMPTS['entity_extraction_system_prompt'] = PROMPTS['entity_extraction_system_prompt'].format(
    entity_types=DACSA_ENTITY_TYPES
)

# Mensaje de confirmación final en los logs
print("\n" + "="*80)
print("✅ CUSTOM PROMPTS LOADED SUCCESSFULLY (v1.1.8 QUIRÚRGICA)")
print("="*80)
print("🔧 CAMBIOS CRÍTICOS v1.1.8:")
print("   - Separación Commodity / Product / CropVariety (elimina ambigüedad)")
print("   - Prohibiciones reforzadas: adjetivos, verbos, roles sin persona")
print("   - Clarificación explícita Process vs Technology")
print("="*80)
print("📋 Mantenido COMPLETO de v1.1.7:")
print("   ✓ Filtros anti-numéricos (t, Tn, kg, M de, millones)")
print("   ✓ Tipo 'Metric' → Solo NOMBRES, no valores")
print("   ✓ Formato oficial: <|#|> delimitador")
print("   ✓ CORPORATE_NORMALIZATIONS")
print("   ✓ Funciones auxiliares completas")
print("="*80)
print("🎯 NUEVA ONTOLOGÍA:")
print("   • Commodity → Rice, Wheat, Corn (materia prima genérica)")
print("   • Product → Arroz Bomba La Fallera (SKU comercializable)")
print("   • CropVariety → Senia, Bomba (variedad agronómica)")
print("   • Process → Blanqueado, Molienda (QUÉ se hace)")
print("   • Technology → Clasificación Óptica (CÓMO se hace)")
print("="*80)
print("❌ AHORA BLOQUEA:")
print("   • Adjetivos: high, quality, efficient, sustainable, premium, fresh")
print("   • Verbos: improve, optimize, reduce, increase, grow, develop")
print("   • Roles: management, team, department, division, staff, board")
print("="*80 + "\n")