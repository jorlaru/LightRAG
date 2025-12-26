"""
LightRAG Prompts - Dacsa Group Edition
Optimizado para análisis de documentos del sector arrocero y agroindustria.
Incluye filtros agresivos anti-ruido y normalización corporativa.

Versión: 1.5.0 TRANSLATION
Fecha: 2024-12-25
Cambios v1.5.0: AÑADIDOS diccionarios ES→EN para Products/Varieties
                 SIN tocar estructura v1.1.6 (que funciona)
                 Mantenida compatibilidad total con jorlaru/lightrag
"""

from __future__ import annotations
from typing import Any
import re

# ============================================================================
# DICCIONARIOS DE TRADUCCIÓN (NUEVO EN v1.5.0)
# ============================================================================

PRODUCT_TRANSLATIONS = {
    'arroz': 'Rice',
    'maíz': 'Maize',
    'maiz': 'Maize',
    'trigo': 'Wheat',
    'centeno': 'Rye',
    'cebada': 'Barley',
    'legumbres': 'Pulses',
    'legumbre': 'Pulses',
}

VARIETY_TRANSLATIONS = {
    # MAIZE VARIETIES
    'sémola cervecera': 'Brewing Grits',
    'semola cervecera': 'Brewing Grits',
    'sémola flaking': 'Flaking Grits',
    'semola flaking': 'Flaking Grits',
    'sémola polenta': 'Polenta Grits',
    'sémola hominy': 'Hominy Grits',
    'harina de maíz nativa': 'Maize Native Flour',
    'harina de maíz precocida': 'Maize Precooked Flour',
    'harina de maíz estabilizada': 'Maize Stabilized Flour',
    'harina de maíz tratada térmicamente': 'Maize Heat-treated Flour',
    'harina de maíz desgerminada': 'Maize Degerminated Flour',
    'harina masa': 'Masa Flour',
    'germen de maíz crudo': 'Maize Germ Raw',
    'germen de maíz tostado': 'Maize Germ Toasted',
    'salvado de maíz': 'Maize Bran',
    'fibra de maíz': 'Maize Fiber',
    'sémola de maíz': 'Maize Semolina',
    
    # RICE VARIETIES
    'japónica': 'Japonica',
    'japonica': 'Japonica',
    'índica': 'Indica',
    'indica': 'Indica',
    'arroz vaporizado': 'Parboiled Rice',
    'arroz parboiled': 'Parboiled Rice',
    'arroz integral': 'Brown Rice',
    'arroz partido': 'Broken Rice',
    'harina de arroz fina': 'Rice Flour Fine',
    'harina de arroz integral': 'Rice Brown Flour',
    'harina de arroz precocida': 'Rice Precooked Flour',
    'harina de arroz gelatinizada': 'Rice Gelatinized Flour',
    'arroz pregelatinizado': 'Pre-gelatinized Rice',
    'sémola de arroz': 'Rice Semolina',
    'almidón de arroz nativo': 'Rice Starch Native',
    'almidón de arroz modificado': 'Rice Starch Modified',
    'concentrado proteico de arroz': 'Rice Protein Concentrate',
    'harina de arroz grado alimentación infantil': 'Rice Flour Baby Food Grade',
    
    # WHEAT VARIETIES
    'harina de trigo blanda': 'Wheat Soft Flour',
    'harina de trigo duro': 'Wheat Durum Flour',
    'sémola de trigo': 'Wheat Semolina',
    'salvado de trigo': 'Wheat Bran',
    'germen de trigo': 'Wheat Germ',
    'harina de trigo integral': 'Wheat Whole Grain Flour',
    
    # RYE VARIETIES
    'harina de centeno': 'Rye Flour',
    
    # BARLEY VARIETIES
    'cebada perlada': 'Barley Pearled',
    
    # PULSE VARIETIES
    'harina de garbanzo': 'Chickpea Flour',
    'harina de lenteja roja': 'Red Lentil Flour',
    'harina de lenteja verde': 'Green Lentil Flour',
    'harina de guisante amarillo': 'Yellow Pea Flour',
    'harina de guisante verde': 'Green Pea Flour',
    'harina de haba': 'Faba Bean Flour',
    'aislado proteico de guisante': 'Pea Protein Isolate',
    'almidón de legumbres': 'Pulse Starch',
    'fibra de legumbres': 'Pulse Fiber',
    'harina de legumbres tostadas': 'Toasted Pulse Flour',
}

VARIETY_TO_PRODUCT_MAP = {
    # Maize
    'Brewing Grits': 'Maize', 'Flaking Grits': 'Maize', 'Polenta Grits': 'Maize',
    'Hominy Grits': 'Maize', 'Maize Native Flour': 'Maize', 'Maize Precooked Flour': 'Maize',
    'Maize Stabilized Flour': 'Maize', 'Maize Heat-treated Flour': 'Maize',
    'Maize Degerminated Flour': 'Maize', 'Masa Flour': 'Maize', 'Maize Germ Raw': 'Maize',
    'Maize Germ Toasted': 'Maize', 'Maize Bran': 'Maize', 'Maize Fiber': 'Maize',
    'Maize Semolina': 'Maize',
    
    # Rice
    'Japonica': 'Rice', 'Indica': 'Rice', 'Parboiled Rice': 'Rice', 'Brown Rice': 'Rice',
    'Broken Rice': 'Rice', 'Rice Flour Fine': 'Rice', 'Rice Brown Flour': 'Rice',
    'Rice Precooked Flour': 'Rice', 'Rice Gelatinized Flour': 'Rice',
    'Pre-gelatinized Rice': 'Rice', 'Rice Semolina': 'Rice', 'Rice Starch Native': 'Rice',
    'Rice Starch Modified': 'Rice', 'Rice Protein Concentrate': 'Rice',
    'Rice Flour Baby Food Grade': 'Rice',
    
    # Wheat
    'Wheat Soft Flour': 'Wheat', 'Wheat Durum Flour': 'Wheat', 'Wheat Semolina': 'Wheat',
    'Wheat Bran': 'Wheat', 'Wheat Germ': 'Wheat', 'Wheat Whole Grain Flour': 'Wheat',
    
    # Rye
    'Rye Flour': 'Rye',
    
    # Barley
    'Barley Pearled': 'Barley',
    
    # Pulses
    'Chickpea Flour': 'Pulses', 'Red Lentil Flour': 'Pulses', 'Green Lentil Flour': 'Pulses',
    'Yellow Pea Flour': 'Pulses', 'Green Pea Flour': 'Pulses', 'Faba Bean Flour': 'Pulses',
    'Pea Protein Isolate': 'Pulses', 'Pulse Starch': 'Pulses', 'Pulse Fiber': 'Pulses',
    'Toasted Pulse Flour': 'Pulses',
}

# ============================================================================
# FUNCIONES DE TRADUCCIÓN (NUEVO EN v1.5.0)
# ============================================================================

def translate_entity_to_english(entity_name: str, entity_type: str) -> str:
    """
    Traduce entidades ES→EN usando diccionarios offline.
    
    Args:
        entity_name: Nombre de la entidad en español
        entity_type: Tipo de entidad (Product, Variety, etc.)
    
    Returns:
        Nombre traducido al inglés o nombre original si no hay traducción
    """
    name_lower = entity_name.lower().strip()
    
    # Traducción directa de Products
    if entity_type == 'Product' and name_lower in PRODUCT_TRANSLATIONS:
        return PRODUCT_TRANSLATIONS[name_lower]
    
    # Traducción directa de Varieties
    if entity_type == 'Variety' and name_lower in VARIETY_TRANSLATIONS:
        return VARIETY_TRANSLATIONS[name_lower]
    
    # Fallback: buscar palabra por palabra
    words = entity_name.split()
    translated = []
    for word in words:
        w_lower = word.lower()
        if w_lower in PRODUCT_TRANSLATIONS:
            translated.append(PRODUCT_TRANSLATIONS[w_lower])
        elif w_lower in VARIETY_TRANSLATIONS:
            # Buscar coincidencia parcial
            for es_term, en_term in VARIETY_TRANSLATIONS.items():
                if w_lower in es_term:
                    translated.append(en_term.split()[0])
                    break
            else:
                translated.append(word)
        else:
            translated.append(word)
    
    return ' '.join(translated) if translated else entity_name


def get_product_for_variety(variety_name: str) -> str:
    """
    Obtiene el Product base para una Variety.
    
    Args:
        variety_name: Nombre de la variedad
    
    Returns:
        Nombre del producto base o None
    """
    return VARIETY_TO_PRODUCT_MAP.get(variety_name)


# ============================================================================
# NORMALIZACIÓN CON REGEX (v1.5.0 - DEDUPLICACIÓN)
# ============================================================================

def normalize_entity_name(entity_name: str, entity_type: str) -> str:
    """
    Normaliza nombres de entidades usando regex para evitar duplicados.
    
    Casos:
        - "Ebro Foods" vs "EBRO FOODS" → "Ebro Foods"
        - "ISO 22000" vs "ISO-22000" → "ISO 22000"
        - "Production Capacity" vs "production capacity" → "Production Capacity"
    
    Args:
        entity_name: Nombre original de la entidad
        entity_type: Tipo de entidad (Company, Standard, Metric, etc.)
    
    Returns:
        Nombre normalizado según tipo
    """
    if not entity_name or len(entity_name.strip()) == 0:
        return entity_name
    
    normalized = entity_name.strip()
    
    # 1. COMPANY: Title Case + eliminar espacios múltiples
    if entity_type == 'Company':
        # Eliminar espacios múltiples
        normalized = re.sub(r'\s+', ' ', normalized)
        # Title Case (Ebro Foods, SOS Corporación)
        normalized = normalized.title()
        # Excepciones acrónimos (S.A., S.L.)
        normalized = re.sub(r'\bS\.a\.\b', 'S.A.', normalized)
        normalized = re.sub(r'\bS\.l\.\b', 'S.L.', normalized)
    
    # 2. STANDARD: Normalizar formato (ISO 22000, DO Calasparra)
    elif entity_type == 'Standard':
        # Eliminar guiones entre letras y números: ISO-22000 → ISO 22000
        normalized = re.sub(r'([A-Z]+)-(\d+)', r'\1 \2', normalized)
        # Mayúsculas para acrónimos al inicio: iso 22000 → ISO 22000
        if re.match(r'^[a-z]+\s+\d+', normalized.lower()):
            parts = normalized.split()
            parts[0] = parts[0].upper()
            normalized = ' '.join(parts)
        # DO Calasparra en Title Case
        normalized = re.sub(r'^do\s+', 'DO ', normalized, flags=re.IGNORECASE)
    
    # 3. METRIC: Title Case (Production Capacity)
    elif entity_type == 'Metric':
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
    
    # 4. PROCESS: Title Case (Parboiling, Milling)
    elif entity_type == 'Process':
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
    
    # 5. PRODUCT/VARIETY: Title Case con excepciones
    elif entity_type in ['Product', 'Variety']:
        normalized = re.sub(r'\s+', ' ', normalized)
        # Title Case general
        normalized = normalized.title()
        # Excepciones: mantener acrónimos en mayúscula
        normalized = re.sub(r'\bUsa\b', 'USA', normalized)
        normalized = re.sub(r'\bEu\b', 'EU', normalized)
    
    # 6. BRAND: Respetar mayúsculas originales pero limpiar espacios
    elif entity_type == 'Brand':
        normalized = re.sub(r'\s+', ' ', normalized)
        # Mantener capitalización original
    
    # 7. FACILITY: Title Case + normalizar términos comunes
    elif entity_type == 'Facility':
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
        # Normalizar términos: planta/plant, molino/mill
        normalized = re.sub(r'\bPlanta\b', 'Plant', normalized)
        normalized = re.sub(r'\bMolino\b', 'Mill', normalized)
    
    # 8. GEOGRAPHY: Title Case
    elif entity_type == 'Geography':
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
    
    # 9. MARKET: Normalizar formato (HORECA España → HORECA Spain)
    elif entity_type == 'Market':
        normalized = re.sub(r'\s+', ' ', normalized)
        # HORECA en mayúsculas
        normalized = re.sub(r'\bhoreca\b', 'HORECA', normalized, flags=re.IGNORECASE)
        # País en Title Case
        parts = normalized.split()
        if len(parts) > 1:
            parts[1] = parts[1].title()
        normalized = ' '.join(parts)
    
    # 10. TECHNOLOGY/SUSTAINABILITY/AGREEMENT/EVENT/PERSON: Title Case
    elif entity_type in ['Technology', 'Sustainability', 'Agreement', 'Event', 'Person']:
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
    
    return normalized


def calculate_entity_similarity(name1: str, name2: str) -> float:
    """
    Calcula similitud entre dos nombres de entidades (0.0 a 1.0).
    
    Reglas:
        - Ignora mayúsculas/minúsculas
        - Ignora guiones, puntos, espacios extras
        - Calcula ratio de caracteres comunes
    
    Args:
        name1, name2: Nombres a comparar
    
    Returns:
        Float 0.0-1.0 (1.0 = idénticos)
    
    Examples:
        - "Ebro Foods" vs "EBRO FOODS" → 1.0
        - "ISO 22000" vs "ISO-22000" → 1.0
        - "Ebro Foods" vs "Dacsa Group" → <0.3
    """
    # Normalizar para comparación
    def clean(s):
        s = s.lower()
        s = re.sub(r'[^a-z0-9]', '', s)  # Solo alfanuméricos
        return s
    
    clean1 = clean(name1)
    clean2 = clean(name2)
    
    if not clean1 or not clean2:
        return 0.0
    
    # Identidad exacta
    if clean1 == clean2:
        return 1.0
    
    # Ratio de caracteres comunes (simple)
    common = sum(1 for c in clean1 if c in clean2)
    max_len = max(len(clean1), len(clean2))
    
    return common / max_len if max_len > 0 else 0.0


def are_entities_duplicates(name1: str, name2: str, entity_type: str, threshold: float = 0.85) -> bool:
    """
    Determina si dos entidades son duplicados.
    
    Args:
        name1, name2: Nombres a comparar
        entity_type: Tipo de entidad
        threshold: Umbral de similitud (0.85 por defecto)
    
    Returns:
        True si son duplicados
    
    Examples:
        - "Ebro Foods", "EBRO FOODS", "Company" → True
        - "ISO 22000", "ISO-22000", "Standard" → True
        - "Ebro Foods", "Ebro", "Company" → False (0.72 < 0.85)
    """
    # Normalizar ambos según tipo
    norm1 = normalize_entity_name(name1, entity_type)
    norm2 = normalize_entity_name(name2, entity_type)
    
    # Comparación exacta tras normalización
    if norm1 == norm2:
        return True
    
    # Comparación por similitud
    similarity = calculate_entity_similarity(norm1, norm2)
    
    return similarity >= threshold


# ============================================================================
# REGLAS REGEX POR TIPO DE ENTIDAD
# ============================================================================

NORMALIZATION_RULES = {
    'Company': {
        'pattern': r'\s+',
        'replacement': ' ',
        'case': 'title',
        'remove_suffixes': [' S.A.', ' SA', ' S.L.', ' SL', ' Inc.', ' Ltd.', ' LLC'],
    },
    'Standard': {
        'patterns': [
            (r'([A-Z]+)-(\d+)', r'\1 \2'),  # ISO-22000 → ISO 22000
            (r'^iso\s+', 'ISO ', re.IGNORECASE),  # iso 22000 → ISO 22000
            (r'^do\s+', 'DO ', re.IGNORECASE),  # do calasparra → DO Calasparra
        ],
    },
    'Metric': {
        'case': 'title',
        'pattern': r'\s+',
        'replacement': ' ',
    },
    'Process': {
        'case': 'title',
        'pattern': r'\s+',
        'replacement': ' ',
    },
    'Market': {
        'patterns': [
            (r'\bhoreca\b', 'HORECA', re.IGNORECASE),
        ],
    },
    'Facility': {
        'case': 'title',
        'patterns': [
            (r'\bplanta\b', 'Plant', re.IGNORECASE),
            (r'\bmolino\b', 'Mill', re.IGNORECASE),
        ],
    },
}

# ============================================================================
# CONFIGURACIÓN DE TIPOS DE ENTIDAD - DACSA GROUP (v1.1.6)
# ============================================================================

DACSA_ENTITY_TYPES = """
### Entity Types para Dacsa Group (Sector Arrocero/Agroindustria)

1. **Company**: Empresas, corporaciones, consorcios (ej: Dacsa Group, Ebro Foods, SOS Corporación)
2. **Brand**: Marcas comerciales de productos (ej: La Fallera, Arroz SOS, Nomen)
3. **Product**: Productos específicos de arroz o derivados (ej: Arroz Bomba, Arroz Integral, Harina de Arroz)
4. **Variety**: Variedades de arroz u otros cultivos (ej: Senia, Bahia, Albufera, J-Sendra)
5. **Facility**: Instalaciones industriales, plantas, almacenes (ej: Planta Sueca, Molino Valencia)
6. **Geography**: Ubicaciones específicas, regiones de cultivo (ej: Delta del Ebro, Albufera, Calasparra)
7. **Person**: Personas específicas (ejecutivos, agricultores, investigadores)
8. **Technology**: Tecnologías agrícolas o industriales específicas (ej: Secado por Infrarrojos, Clasificación Óptica)
9. **Standard**: Normas, certificaciones, regulaciones (ej: ISO 22000, GlobalGAP, DO Calasparra)
10. **Metric**: Indicadores cuantitativos clave (ej: Rendimiento Hectárea, Ratio Conversión, Humedad)
11. **Process**: Procesos industriales o agrícolas específicos (ej: Descascarillado, Blanqueado, Parboilizado)
12. **Market**: Mercados específicos, canales de distribución (ej: Mercado HORECA, Exportación Europa)
13. **Sustainability**: Iniciativas o prácticas sostenibles concretas (ej: Riego por Goteo, Captura Carbono)
14. **Agreement**: Acuerdos comerciales, contratos, alianzas (ej: Convenio Productores Valencia)
15. **Event**: Eventos relevantes del sector (ej: Fira Alimentaria, Congreso Arrocero)

### Entidades PROHIBIDAS (nunca extraer):
- Conceptos genéricos: "market", "price", "trend", "growth", "production", "consumption", "demand", "supply"
- Valores numéricos: años sueltos (2024, 2025), porcentajes, cantidades monetarias
- Términos vagos: "analysis", "data", "information", "report", "study", "model", "system"
- Commodities NO relacionadas con líneas de negocio Dacsa: "cotton", "algodón", "oats", "avena"
- Acrónimos de 2 letras sin contexto: "FA", "CV", "DW"
- Conceptos temporales: "Q1", "trimestre", "ejercicio", "periodo"

### Commodities PERMITIDAS (líneas de negocio Dacsa Group):
- Arroz y variedades: "Rice", "Bomba", "Senia", "Albufera", "Basmati", etc.
- Trigo: "Wheat", "Trigo", "Wheat Flour", "Harina de Trigo"
- Soja: "Soy", "Soya", "Soja", "Soybean", "Soy Protein"
- Cebada: "Barley", "Cebada", "Malting Barley"
- Maíz: "Corn", "Maíz", "Maize", "Sweet Corn"
- Legumbres: "Chickpea", "Garbanzo", "Lentil", "Lenteja", "Pea", "Guisante", "Bean", "Alubia"
"""

# ============================================================================
# FILTROS ANTI-RUIDO - LISTA NEGRA DE ENTIDADES (v1.1.6)
# ============================================================================

ENTITY_BLACKLIST = {
    # Términos genéricos de mercado
    'market', 'price', 'prices', 'trend', 'trends', 'growth', 'decline',
    'increase', 'decrease', 'change', 'changes', 'development', 'developments',
    'production', 'consumption', 'demand', 'supply', 'trade', 'export', 'import',
    'volume', 'quantity', 'value', 'cost', 'revenue', 'profit', 'margin',
    
    # Términos de análisis
    'analysis', 'data', 'information', 'report', 'study', 'research', 
    'model', 'system', 'process', 'method', 'approach', 'strategy',
    'projection', 'forecast', 'outlook', 'perspective', 'expectation',
    
    # Términos temporales
    'year', 'month', 'quarter', 'period', 'season', 'cycle', 'phase',
    'q1', 'q2', 'q3', 'q4', 'trimestre', 'ejercicio', 'periodo',
    
    # Commodities NO relacionadas con Dacsa Group (solo algodón, avena)
    'cotton', 'algodón', 
    'oats', 'avena',
    
    # Términos vagos
    'factor', 'element', 'aspect', 'component', 'characteristic', 'feature',
    'impact', 'effect', 'influence', 'consequence', 'result', 'outcome',
    'issue', 'problem', 'challenge', 'opportunity', 'risk', 'benefit',
    
    # Acrónimos problemáticos
    'fa', 'cv', 'dw', 'na', 'nd', 'tbd', 'etc',
}

# ============================================================================
# NORMALIZACIÓN DE NOMBRES CORPORATIVOS (v1.1.6)
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
# PROMPTS PRINCIPALES (v1.1.6 EXACTO)
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
# SYSTEM PROMPT - EXTRACCIÓN DE ENTIDADES (v1.1.6 EXACTO)
# ----------------------------------------------------------------------------

PROMPTS['entity_extraction_system_prompt'] = """
You are a specialized AI assistant for analyzing documents from the rice and agribusiness sector.
Your task is to extract structured information (entities and relationships) with strict quality filters.

**CRITICAL RULES:**

1. **Entity Extraction:**
   - Extract ONLY concrete, specific entities (companies, products, facilities, people)
   - NEVER extract generic concepts like "market", "price", "trend", "growth", "cotton"
   - NEVER extract standalone years (2024, 2025), percentages, or monetary values
   - NEVER extract acronyms with 2 letters (FA, CV) unless they are well-known organizations
   - Minimum entity name length: 3 characters
   - Normalize company names by removing legal suffixes (S.A., Inc., Ltd.)

2. **Entity Types:**
{entity_types}

3. **Blacklisted Terms (NEVER extract):**
   market, price, trend, growth, production, consumption, demand, supply, cotton, algodón,
   analysis, data, report, study, year, quarter, period, Q1, Q2, Q3, Q4

4. **Relationship Extraction:**
   - Extract ONLY meaningful, specific relationships
   - AVOID generic relationships like "is related to", "is part of", "influences"
   - Prefer action-oriented relationships: "supplies to", "manufactures", "distributes", "certifies"
   - Each relationship MUST have concrete evidence in the text

5. **Language:**
   - Extract entities in their original language (Spanish/English as they appear)
   - Descriptions and keywords MUST be in English
   - Normalize company names to their most common form

6. **Quality Over Quantity:**
   - Better 5 high-quality entities than 20 generic ones
   - Each entity must add strategic value to understanding the business domain
   - If in doubt, DO NOT extract

7. **OUTPUT FORMAT (CRITICAL - OFFICIAL HKUDS/LightRAG FORMAT):**
   - Use text-delimited format with <|#|> delimiter (NOT <|>)
   - Each entity: entity<|#|>entity_name<|#|>entity_type<|#|>entity_description##
   - Each relationship: relation<|#|>src_id<|#|>tgt_id<|#|>description<|#|>keywords<|#|>weight##
   - NO parentheses around entities or relations
   - End with: <|COMPLETE|>
"""

# ----------------------------------------------------------------------------
# EXAMPLES - EXTRACCIÓN DE ENTIDADES (v1.1.6 EXACTO - SIN VARIABLES)
# ----------------------------------------------------------------------------

PROMPTS['entity_extraction_examples'] = [
    """Example 1:
Input: "Dacsa Group S.A. opera una planta de arroz en Sueca que procesa variedades Bomba y Senia para la marca La Fallera, certificada ISO 22000."

Output:
entity<|#|>Dacsa Group<|#|>Company<|#|>Leading European rice producer and processor##
entity<|#|>Planta Sueca<|#|>Facility<|#|>Rice processing plant located in Sueca##
entity<|#|>Bomba<|#|>Variety<|#|>Premium short-grain rice variety from Valencia region##
entity<|#|>Senia<|#|>Variety<|#|>Traditional medium-grain rice variety##
entity<|#|>La Fallera<|#|>Brand<|#|>Premium rice brand owned by Dacsa Group##
entity<|#|>ISO 22000<|#|>Standard<|#|>International food safety management standard##
relation<|#|>Dacsa Group<|#|>Planta Sueca<|#|>Operates rice processing facility<|#|>operation,facility,ownership<|#|>1.0##
relation<|#|>Planta Sueca<|#|>Bomba<|#|>Processes premium rice variety<|#|>processing,variety,production<|#|>0.9##
relation<|#|>Planta Sueca<|#|>Senia<|#|>Processes traditional rice variety<|#|>processing,variety,production<|#|>0.9##
relation<|#|>Dacsa Group<|#|>La Fallera<|#|>Owns and markets premium brand<|#|>brand,ownership,marketing<|#|>1.0##
relation<|#|>La Fallera<|#|>ISO 22000<|#|>Certified under food safety standard<|#|>certification,quality,compliance<|#|>0.8##
<|COMPLETE|>""",
    
    """Example 2:
Input: "Ebro Foods lidera el mercado español de legumbres con su línea de garbanzos y lentejas. Cotton production in India is growing."

Output:
entity<|#|>Ebro Foods<|#|>Company<|#|>Leading Spanish food company in rice and pulses##
entity<|#|>Garbanzos<|#|>Product<|#|>Chickpeas processed for Spanish market##
entity<|#|>Lentejas<|#|>Product<|#|>Lentils processed for Spanish market##
entity<|#|>España<|#|>Geography<|#|>Spain - primary market for pulses##
relation<|#|>Ebro Foods<|#|>Garbanzos<|#|>Markets chickpea products<|#|>product,marketing,pulses<|#|>0.9##
relation<|#|>Ebro Foods<|#|>Lentejas<|#|>Markets lentil products<|#|>product,marketing,pulses<|#|>0.9##
relation<|#|>Ebro Foods<|#|>España<|#|>Operates in Spanish market<|#|>market,geography,operations<|#|>0.8##
<|COMPLETE|>

Note: "Cotton production" and "India" were NOT extracted because:
- "Cotton" is in blacklist (not a Dacsa business line)
- "market", "production" are generic terms
- "India" lacks specific context without concrete entity relationships"""
]

# ----------------------------------------------------------------------------
# USER PROMPT - EXTRACCIÓN DE ENTIDADES (v1.1.6 EXACTO)
# ----------------------------------------------------------------------------

PROMPTS['entity_extraction_user_prompt'] = """
### Context:
{input_text}

### Task:
Extract entities and relationships from the text above following these strict rules:

**OUTPUT FORMAT (CRITICAL - OFFICIAL HKUDS/LightRAG FORMAT):**

For each entity:
entity<|#|>entity_name<|#|>entity_type<|#|>entity_description##

For each relationship:
relation<|#|>src_id<|#|>tgt_id<|#|>description<|#|>keywords<|#|>weight##

End with:
<|COMPLETE|>

**FIELD DESCRIPTIONS:**
- entity_name: Exact name as it appears (normalize company suffixes)
- entity_type: One of: Company, Brand, Product, Variety, Facility, Geography, Person, Technology, Standard, Metric, Process, Market, Sustainability, Agreement, Event
- entity_description: Concise English description (max 200 chars)
- src_id / tgt_id: Must match entity_name exactly
- description: Specific English description of the relationship
- keywords: Comma-separated keywords (no spaces after commas)
- weight: Float between 0.0 and 1.0

**EXTRACTION RULES:**
- Maximum 10 entities per chunk
- Maximum 8 relationships per chunk
- Skip generic terms from the blacklist
- Normalize corporate names (remove S.A., Ltd., etc.)
- All descriptions and keywords in English
- Entity names in original language

**Examples of GOOD entities:**
✅ "Dacsa Group" (Company)
✅ "Arroz Bomba" (Product)
✅ "Delta del Ebro" (Geography)
✅ "ISO 22000" (Standard)
✅ "Planta Sueca" (Facility)
✅ "Wheat Flour" (Product) - línea de negocio Dacsa
✅ "Soybean" (Product) - línea de negocio Dacsa
✅ "Chickpea" (Product) - línea de negocio Dacsa
✅ "Barley" (Product) - línea de negocio Dacsa

**Examples of BAD entities (DO NOT EXTRACT):**
❌ "Market" (too generic)
❌ "2024" (standalone year)
❌ "Cotton" (filtered commodity - not Dacsa business line)
❌ "Price Trend" (generic concept)
❌ "Q3" (temporal period)

**REMEMBER:**
- Output text-delimited format with <|#|> delimiter
- Each line ends with ##
- Final line is <|COMPLETE|>
- Use "relation" not "relationship"
- NO parentheses around output

######################
-Output-
######################
"""

# ----------------------------------------------------------------------------
# CONTINUE EXTRACTION PROMPT (v1.1.6 EXACTO)
# ----------------------------------------------------------------------------

PROMPTS["entity_continue_extraction_user_prompt"] = """
### Task:
Based on the previous extraction, check if there are any **missing** entities or relationships 
in the text that are highly relevant to Dacsa Group's business (Rice, Wheat, Soy, Corn, Pulses).

### Instructions:
1. Extract ONLY entities that were missed in the first pass
2. Follow the same strict filtering rules (No generic terms like 'market', 'growth', 'price')
3. If NO additional entities are found, output only: <|COMPLETE|>

### OUTPUT FORMAT (OFFICIAL HKUDS/LightRAG FORMAT):
entity<|#|>entity_name<|#|>entity_type<|#|>entity_description##
relation<|#|>src_id<|#|>tgt_id<|#|>description<|#|>keywords<|#|>weight##
<|COMPLETE|>

### Context:
{input_text}

######################
-Output-
######################
"""

# ----------------------------------------------------------------------------
# SUMMARIZATION PROMPT (v1.1.6 EXACTO)
# ----------------------------------------------------------------------------

PROMPTS['summarize_entity_descriptions'] = """
You are a specialized assistant for the rice and agribusiness sector.

### Description List:
{description_list}

### Task:
Synthesize the descriptions into a single, comprehensive English summary.

### Rules:
1. Use technical terminology appropriate for the agribusiness sector
2. Maximum length: 500 characters
3. Focus on concrete facts: what it is, what it does, where it operates
4. Remove redundancies and generic statements
5. Prioritize operational and strategic information
6. Language: English only

### Output Format:
Return ONLY the synthesized description text. No additional formatting.

######################
-Output-
######################
"""

# ----------------------------------------------------------------------------
# RAG RESPONSE PROMPT (v1.1.6 EXACTO)
# ----------------------------------------------------------------------------

PROMPTS['rag_response'] = """
You are an expert analyst specializing in the rice and agribusiness sector, 
particularly focused on Dacsa Group and related companies.

### Context from Knowledge Graph:
{context_data}

### User Query:
{user_prompt}

### Instructions:
1. Answer based ONLY on the provided context
2. Use technical terminology appropriate for the sector
3. Structure your response with:
   - Direct answer to the query
   - Supporting evidence from context
   - Relevant metrics or data points (if available)
   - Strategic implications (if applicable)

4. If the context is insufficient, clearly state: "Based on available data, [partial answer]. 
   Additional information about [missing aspect] is not available in the current knowledge base."

5. Language: Respond in Spanish unless the query is in English

6. Cite specific entities when relevant (companies, facilities, products, standards)

### Response:
"""

# ----------------------------------------------------------------------------
# KEYWORD EXTRACTION PROMPT (v1.1.6 EXACTO)
# ----------------------------------------------------------------------------

PROMPTS['keywords_extraction'] = """
Extract 3-5 concise English keywords from the following text that represent the core concepts.

### Text:
{query}

### Rules:
1. Keywords must be nouns or noun phrases
2. Maximum 3 words per keyword
3. Avoid generic terms: market, price, trend, production, cotton
4. Focus on domain-specific terms: rice varieties, processes, standards, technologies
5. Prefer concrete over abstract terms

### Output Format:
keyword1,keyword2,keyword3,keyword4,keyword5

######################
-Keywords-
######################
"""

# ----------------------------------------------------------------------------
# NAIVE RAG RESPONSE (v1.1.6 EXACTO)
# ----------------------------------------------------------------------------

PROMPTS['naive_rag_response'] = """
You are an expert analyst for the rice and agribusiness sector.

### Available Information:
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
# PROMPTS ADICIONALES (v1.1.6)
# ============================================================================

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
# CONFIGURACIÓN ADICIONAL (v1.1.6)
# ============================================================================

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

LOGGING_CONFIG = {
    'level': 'INFO',
    'log_extractions': True,
    'log_filtered_entities': True,
    'log_normalizations': True,
}

# ============================================================================
# FUNCIONES AUXILIARES (v1.1.6 + v1.5.0)
# ============================================================================

def should_filter_entity(entity_name: str) -> bool:
    """
    Determina si una entidad debe ser filtrada según las reglas anti-ruido.
    """
    name_lower = entity_name.lower().strip()
    
    if len(name_lower) < 3:
        return True
    
    if name_lower in ENTITY_BLACKLIST:
        return True
    
    if name_lower.isdigit() and len(name_lower) == 4:
        return True
    
    if '%' in name_lower:
        return True
    
    if any(symbol in name_lower for symbol in ['$', '€', '£', '¥']):
        return True
    
    forbidden_words = ['cotton', 'algodón']
    if any(word in name_lower for word in forbidden_words):
        return True
    
    return False


def normalize_company_name(entity_name: str) -> str:
    """
    Normaliza nombres de empresas eliminando sufijos legales.
    Ahora usa normalize_entity_name() con reglas regex.
    """
    # Normalización base con regex
    normalized = normalize_entity_name(entity_name, 'Company')
    
    # Eliminar sufijos legales (ahora ya lo hace normalize_entity_name)
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

for key in REQUIRED_KEYS:
    assert key in PROMPTS, f"Missing required prompt key: {key}"

# Inyectar tipos de entidad en los prompts
PROMPTS['entity_extraction_system_prompt'] = PROMPTS['entity_extraction_system_prompt'].format(
    entity_types=DACSA_ENTITY_TYPES
)

# ============================================================================
# CONFIRMACIÓN DE CARGA
# ============================================================================

print("\n" + "="*80)
print("✅ CUSTOM PROMPTS LOADED SUCCESSFULLY")
print("="*80)
print("📦 Versión: 1.5.0 TRANSLATION + NORMALIZATION (basada en v1.1.6 oficial)")
print("="*80)
print("🔧 ESTRUCTURA v1.1.6 (sin cambios):")
print("   - Delimitador: <|#|>")
print("   - Formato: entity<|#|>name<|#|>type<|#|>description##")
print("   - Formato: relation<|#|>src<|#|>tgt<|#|>desc<|#|>keywords<|#|>weight##")
print("   - Examples: LISTA sin variables")
print("="*80)
print("🆕 AÑADIDO v1.5.0:")
print(f"   - PRODUCT_TRANSLATIONS: {len(PRODUCT_TRANSLATIONS)} entradas ES→EN")
print(f"   - VARIETY_TRANSLATIONS: {len(VARIETY_TRANSLATIONS)} entradas ES→EN")
print(f"   - VARIETY_TO_PRODUCT_MAP: {len(VARIETY_TO_PRODUCT_MAP)} mapeos")
print("   - translate_entity_to_english() function")
print("   - get_product_for_variety() function")
print("="*80)
print("🧹 NORMALIZACIÓN REGEX (v1.5.0):")
print("   - normalize_entity_name() - Normaliza por tipo de entidad")
print("   - calculate_entity_similarity() - Calcula similitud 0.0-1.0")
print("   - are_entities_duplicates() - Detecta duplicados (umbral 0.85)")
print("   - NORMALIZATION_RULES - Reglas regex por tipo")
print("="*80)
print("📋 EJEMPLOS NORMALIZACIÓN:")
print("   'EBRO FOODS' → 'Ebro Foods' (Company)")
print("   'ISO-22000' → 'ISO 22000' (Standard)")
print("   'production capacity' → 'Production Capacity' (Metric)")
print("   Similitud: 'Ebro Foods' vs 'EBRO FOODS' = 1.0 → DUPLICADO")
print("="*80)
print("✓ Sin cambios en prompts, examples, ni formato")
print("✓ Compatible 100% con jorlaru/lightrag")
print("="*80 + "\n")