"""
LightRAG Prompts - Dacsa Group Edition

Versión: 1.5.0.1 TRANSLATION + NORMALIZATION (CHANNEL KEYERROR FIX)
Fecha: 2024-12-26
FIX: Eliminado conflicto KeyError 'Channel' en definición de Market
"""

from __future__ import annotations
from typing import Any
import re

# ============================================================================
# PRODUCT-VARIETY HIERARCHY (v1.4.0)
# ============================================================================

PRODUCT_WHITELIST = {
    'Rice', 'Maize', 'Wheat', 'Rye', 'Barley', 'Pulses',
}

VARIETY_WHITELIST = {
    # MAIZE (15)
    'Brewing Grits', 'Flaking Grits', 'Polenta Grits', 'Hominy Grits',
    'Maize Native Flour', 'Maize Precooked Flour', 'Maize Stabilized Flour',
    'Maize Heat-treated Flour', 'Maize Degerminated Flour', 'Masa Flour',
    'Maize Germ Raw', 'Maize Germ Toasted', 'Maize Bran', 'Maize Fiber', 'Maize Semolina',
    
    # RICE (15)
    'Japonica', 'Indica', 'Parboiled Rice', 'Brown Rice', 'Broken Rice',
    'Rice Flour Fine', 'Rice Brown Flour', 'Rice Precooked Flour',
    'Rice Gelatinized Flour', 'Pre-gelatinized Rice', 'Rice Semolina',
    'Rice Starch Native', 'Rice Starch Modified', 'Rice Protein Concentrate',
    'Rice Flour Baby Food Grade',
    
    # WHEAT/RYE/BARLEY (8)
    'Wheat Soft Flour', 'Wheat Durum Flour', 'Wheat Semolina',
    'Wheat Bran', 'Wheat Germ', 'Wheat Whole Grain Flour',
    'Rye Flour', 'Barley Pearled',
    
    # PULSES (10)
    'Chickpea Flour', 'Red Lentil Flour', 'Green Lentil Flour',
    'Yellow Pea Flour', 'Green Pea Flour', 'Faba Bean Flour',
    'Pea Protein Isolate', 'Pulse Starch', 'Pulse Fiber', 'Toasted Pulse Flour',
}

VARIETY_TO_PRODUCT_MAP = {
    'Brewing Grits': 'Maize', 'Flaking Grits': 'Maize', 'Polenta Grits': 'Maize',
    'Hominy Grits': 'Maize', 'Maize Native Flour': 'Maize', 'Maize Precooked Flour': 'Maize',
    'Maize Stabilized Flour': 'Maize', 'Maize Heat-treated Flour': 'Maize',
    'Maize Degerminated Flour': 'Maize', 'Masa Flour': 'Maize',
    'Maize Germ Raw': 'Maize', 'Maize Germ Toasted': 'Maize',
    'Maize Bran': 'Maize', 'Maize Fiber': 'Maize', 'Maize Semolina': 'Maize',
    
    'Japonica': 'Rice', 'Indica': 'Rice', 'Parboiled Rice': 'Rice',
    'Brown Rice': 'Rice', 'Broken Rice': 'Rice', 'Rice Flour Fine': 'Rice',
    'Rice Brown Flour': 'Rice', 'Rice Precooked Flour': 'Rice',
    'Rice Gelatinized Flour': 'Rice', 'Pre-gelatinized Rice': 'Rice',
    'Rice Semolina': 'Rice', 'Rice Starch Native': 'Rice',
    'Rice Starch Modified': 'Rice', 'Rice Protein Concentrate': 'Rice',
    'Rice Flour Baby Food Grade': 'Rice',
    
    'Wheat Soft Flour': 'Wheat', 'Wheat Durum Flour': 'Wheat',
    'Wheat Semolina': 'Wheat', 'Wheat Bran': 'Wheat', 'Wheat Germ': 'Wheat',
    'Wheat Whole Grain Flour': 'Wheat', 'Rye Flour': 'Rye',
    'Barley Pearled': 'Barley',
    
    'Chickpea Flour': 'Pulses', 'Red Lentil Flour': 'Pulses',
    'Green Lentil Flour': 'Pulses', 'Yellow Pea Flour': 'Pulses',
    'Green Pea Flour': 'Pulses', 'Faba Bean Flour': 'Pulses',
    'Pea Protein Isolate': 'Pulses', 'Pulse Starch': 'Pulses',
    'Pulse Fiber': 'Pulses', 'Toasted Pulse Flour': 'Pulses',
}

# ============================================================================
# TRANSLATION ES→EN (v1.5.0)
# ============================================================================

PRODUCT_TRANSLATIONS = {
    'arroz': 'Rice', 'maíz': 'Maize', 'maiz': 'Maize',
    'trigo': 'Wheat', 'centeno': 'Rye', 'cebada': 'Barley',
    'legumbres': 'Pulses', 'legumbre': 'Pulses',
}

VARIETY_TRANSLATIONS = {
    'sémola cervecera': 'Brewing Grits', 'semola cervecera': 'Brewing Grits',
    'sémola flaking': 'Flaking Grits', 'sémola polenta': 'Polenta Grits',
    'harina de maíz nativa': 'Maize Native Flour', 'harina de maiz nativa': 'Maize Native Flour',
    'japónica': 'Japonica', 'japonica': 'Japonica', 'índica': 'Indica', 'indica': 'Indica',
    'arroz vaporizado': 'Parboiled Rice', 'arroz integral': 'Brown Rice',
    'harina de arroz fina': 'Rice Flour Fine', 'harina de trigo blando': 'Wheat Soft Flour',
    'harina de garbanzo': 'Chickpea Flour', 'harina de lenteja roja': 'Red Lentil Flour',
}

# ============================================================================
# WHITELISTS (v1.4.0)
# ============================================================================

METRIC_WHITELIST = {
    'Production Capacity', 'Production Volume', 'Processing Capacity',
    'Storage Capacity', 'Yield Rate', 'Moisture Content', 'Protein Content',
    'Broken Grain Rate', 'Revenue', 'EBITDA', 'Operating Margin',
    'Market Share', 'Sales Volume', 'Unit Price', 'Energy Consumption',
    'Water Consumption', 'Waste Reduction', 'Delivery Time',
    'Inventory Turnover', 'Supplier Lead Time',
}

PROCESS_WHITELIST = {
    'Hulling', 'Milling', 'Parboiling', 'Drying', 'Cleaning', 'Sorting',
    'Grinding', 'Sieving', 'Blending', 'Fortification', 'Coating',
    'Packaging', 'Palletizing', 'Loading', 'Quality Testing',
    'Metal Detection', 'Visual Inspection',
}

MARKET_CHANNELS = {'HORECA', 'Retail', 'Foodservice', 'Industrial', 'Export'}
MARKET_COUNTRIES = {
    'Spain', 'France', 'Germany', 'Italy', 'Portugal', 'UK',
    'Netherlands', 'Belgium', 'USA', 'China', 'Japan', 'India',
    'Brazil', 'Mexico'
}

TECHNOLOGY_KEYWORDS = [
    'Optical Sorting', 'Color Sorter', 'Metal Detector',
    'Infrared Dryer', 'Parboiling System', 'Milling System',
    'Packaging Line', 'Automation System', 'Quality Control System',
    'Conveyor System', 'Storage Silo', 'Weighing System'
]

# ============================================================================
# ENTITY TYPES (v1.5.0.1 - CHANNEL FIX)
# ============================================================================

DACSA_ENTITY_TYPES = """
### Entity Types para Dacsa Group (v1.5.0.1 - CHANNEL FIX)

**CRITICAL: ALL entities must be extracted in ENGLISH.**

═══════════════════════════════════════════════════════════════════════════

## 1. COMPANY
Named business entities. Examples: Dacsa Group, Ebro Foods

## 2. BRAND
Commercial brand names. Examples: La Fallera, Nomen

## 3. PRODUCT (6 commodities ONLY)
WHITELIST: Rice, Maize, Wheat, Rye, Barley, Pulses
Extract ONLY if generic product without variety.
If Variety extracted → Product AUTO-EXTRACTED.

## 4. VARIETY (65 specifications)
**MAIZE varieties (15):**
{maize_varieties}

**RICE varieties (15):**
{rice_varieties}

**WHEAT/RYE/BARLEY varieties (8):**
{wheat_varieties}

**PULSES varieties (10):**
{pulse_varieties}

RULE: When extracting Variety → Product AUTO-EXTRACTED + create relationship.

## 5. FACILITY
Named/located industrial installations. Examples: Sueca Plant, Valencia Mill

## 6. PERSON
Named individuals. Extract NAME ONLY (no role in entity_name).

## 7. TECHNOLOGY
Industrial processing technology. Keywords: {technology_keywords}

## 8. METRIC (20 KPIs ONLY)
WHITELIST:
{metric_whitelist}

Extract metric NAME only, never values.

## 9. PROCESS (17 processes ONLY)
WHITELIST:
{process_whitelist}

## 10. MARKET (Channel + Country)
**MANDATORY FORMAT:** "ChannelName CountryName"

**Valid distribution channels:**
   HORECA, Retail, Foodservice, Industrial, Export

**Valid countries:**
   Spain, France, Germany, Italy, Portugal, UK, Netherlands, Belgium,
   USA, China, Japan, India, Brazil, Mexico

**Examples:**
- ✅ "HORECA Spain"
- ✅ "Retail Germany"
- ❌ "HORECA" (channel alone - must have country)
- ❌ "Spain" (country alone - must have channel)

═══════════════════════════════════════════════════════════════════════════
"""

# ============================================================================
# FILTERS
# ============================================================================

ENTITY_BLACKLIST = {
    'market', 'markets', 'price', 'prices', 'trend', 'trends',
    'growth', 'production', 'consumption', 'demand', 'supply',
    'quality', 'efficiency', 'analysis', 'data', 'information',
    'report', 'study', 'year', 'month', 'quarter', 'q1', 'q2', 'q3', 'q4',
    'cotton', 'algodón', 'oats', 'avena', 'factor', 'element',
}

CORPORATE_NORMALIZATIONS = {
    'suffixes': [' S.A.', ' SA', ' S.L.', ' Inc.', ' Ltd.', ' LLC',
                 ' Corp.', ' GmbH', ' AG'],
    'dacsa_aliases': {
        'Dacsa S.A.': 'Dacsa Group',
        'Dacsa SA': 'Dacsa Group',
        'Grupo Dacsa': 'Dacsa Group',
        'DACSA': 'Dacsa Group',
    },
}

SPANISH_TO_ENGLISH = {
    'arroz': 'rice', 'maíz': 'maize', 'trigo': 'wheat',
    'centeno': 'rye', 'cebada': 'barley', 'legumbres': 'pulses',
    'planta': 'Plant', 'molino': 'Mill', 'almacén': 'Warehouse',
}

# ============================================================================
# PROMPTS
# ============================================================================

PROMPTS = {}

PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##\n"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["entity_extraction_func"] = None

PROMPTS['entity_extraction_system_prompt'] = """
You are a specialized AI for rice/agribusiness document analysis.
Extract entities and relationships with strict quality filters.

### ENTITY TYPES:
{entity_types}

### EXTRACTION RULES:
1. ALL entities in ENGLISH (translate Spanish)
2. Skip blacklist terms, numbers, percentages, years
3. Company: Remove legal suffixes
4. Person: Name only (no role)
5. Product: 6 base commodities
6. Variety: 65 specs → auto-extract Product
7. Metric: 20 KPIs
8. Process: 17 operations
9. Market: Must be "Channel Country"

### OUTPUT FORMAT:
entity<|#|>entity_name<|#|>entity_type<|#|>entity_description##
relation<|#|>src_id<|#|>tgt_id<|#|>description<|#|>keywords<|#|>weight##
<|COMPLETE|>

Max 10 entities, 8 relationships per chunk.
"""

PROMPTS['entity_extraction_user_prompt'] = """
### Context:
{input_text}

### Task:
Extract entities and relationships following system prompt rules.
Max 10 entities, 8 relationships. All in English.

######################
-Output-
######################
"""

PROMPTS['entity_continue_extraction_user_prompt'] = """
### Previous extraction:
{previously_extracted_entities}

### Context:
{input_text}

### Task:
Extract NEW entities not in previous extraction.
Max 10 entities, 8 relationships.

######################
-Output-
######################
"""

PROMPTS['entity_extraction_examples'] = [
    """Example 1:
######################
entity<|#|>Dacsa Group<|#|>Company<|#|>Leading rice processor##
entity<|#|>Rice<|#|>Product<|#|>Base commodity##
entity<|#|>Japonica<|#|>Variety<|#|>Short-grain rice##
entity<|#|>Sueca Plant<|#|>Facility<|#|>Main processing facility##
relation<|#|>Dacsa Group<|#|>Sueca Plant<|#|>Operates<|#|>operations,facility<|#|>0.9##
relation<|#|>Japonica<|#|>Rice<|#|>Variety of<|#|>variety,product<|#|>0.95##
<|COMPLETE|>
"""
]

PROMPTS['summarize_entity_descriptions'] = """
Summarize entity descriptions from multiple sources.

Entities:
{entity_name} ({entity_type}):
{description_list}

Create consolidated description (max 200 chars):
"""

PROMPTS['rag_response'] = """
Answer question using knowledge graph context.

Question: {query_prompt}
Context: {content_data}

Answer:
"""

PROMPTS['keywords_extraction'] = """
Extract 3-7 keywords from query.

Query: {query_prompt}

Keywords (comma-separated):
"""

PROMPTS['naive_rag_response'] = """
Answer question using context.

Question: {query_prompt}
Context: {content_data}

Answer:
"""

# ============================================================================
# FUNCTIONS (v1.5.0)
# ============================================================================

def translate_entity_to_english(entity_name: str, entity_type: str) -> str:
    """Traduce ES→EN offline"""
    name_lower = entity_name.lower()
    
    if entity_type == 'Product' and name_lower in PRODUCT_TRANSLATIONS:
        return PRODUCT_TRANSLATIONS[name_lower]
    
    if entity_type == 'Variety' and name_lower in VARIETY_TRANSLATIONS:
        return VARIETY_TRANSLATIONS[name_lower]
    
    if entity_type in ['Company', 'Brand']:
        return normalize_company_name(entity_name)
    
    return entity_name

def normalize_entity_name(entity_name: str, entity_type: str) -> str:
    """Normaliza nombres por tipo"""
    translated = translate_entity_to_english(entity_name, entity_type)
    
    if entity_type == 'Company':
        return normalize_company_name(translated)
    elif entity_type == 'Person':
        return translated.split(',')[0].strip().title()
    elif entity_type in ['Product', 'Variety']:
        return translated.title()
    
    return translated.strip()

def calculate_entity_similarity(name1: str, name2: str, entity_type: str) -> float:
    """Calcula similitud 0.0-1.0"""
    norm1 = normalize_entity_name(name1, entity_type)
    norm2 = normalize_entity_name(name2, entity_type)
    
    if norm1.lower() == norm2.lower():
        return 1.0
    
    if entity_type in ['Company', 'Person']:
        return 0.0
    
    set1 = set(norm1.lower().split())
    set2 = set(norm2.lower().split())
    
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    return 2.0 * intersection / (len(set1) + len(set2))

def are_entities_duplicates(name1: str, name2: str, entity_type: str, threshold: float = 0.85) -> bool:
    """Detecta duplicados"""
    return calculate_entity_similarity(name1, name2, entity_type) >= threshold

def is_numeric_entity(entity_name: str) -> bool:
    """Detecta entidades numéricas a filtrar"""
    if re.match(r'^(19|20)\d{2}$', entity_name):
        return True
    if re.search(r'\d+([.,]\d+)?\s*%', entity_name):
        return True
    if re.search(r'[€$£¥]\s*\d', entity_name):
        return True
    if re.match(r'^\d', entity_name):
        return True
    return False

def normalize_company_name(entity_name: str) -> str:
    """Normaliza nombres corporativos"""
    normalized = entity_name.strip()
    for suffix in CORPORATE_NORMALIZATIONS['suffixes']:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)].strip()
    if normalized in CORPORATE_NORMALIZATIONS['dacsa_aliases']:
        normalized = CORPORATE_NORMALIZATIONS['dacsa_aliases'][normalized]
    return normalized

def is_valid_market(entity_name: str) -> bool:
    """Valida Market format"""
    parts = entity_name.split()
    if len(parts) != 2:
        return False
    channel, country = parts
    return channel in MARKET_CHANNELS and country in MARKET_COUNTRIES

def is_valid_metric(entity_name: str) -> bool:
    return entity_name in METRIC_WHITELIST

def is_valid_process(entity_name: str) -> bool:
    return entity_name in PROCESS_WHITELIST

def is_valid_product(entity_name: str) -> bool:
    return entity_name in PRODUCT_WHITELIST

def is_valid_variety(entity_name: str) -> bool:
    return entity_name in VARIETY_WHITELIST

def get_product_for_variety(variety_name: str) -> str:
    """Retorna Product base para Variety"""
    return VARIETY_TO_PRODUCT_MAP.get(variety_name)

# ============================================================================
# VALIDACIÓN E INYECCIÓN
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

# Preparar listas
maize_varieties_list = '\n'.join(f'   - {v}' for v in sorted([
    'Brewing Grits', 'Flaking Grits', 'Polenta Grits', 'Hominy Grits',
    'Maize Native Flour', 'Maize Precooked Flour', 'Maize Stabilized Flour',
    'Maize Heat-treated Flour', 'Maize Degerminated Flour', 'Masa Flour',
    'Maize Germ Raw', 'Maize Germ Toasted', 'Maize Bran', 'Maize Fiber', 'Maize Semolina'
]))

rice_varieties_list = '\n'.join(f'   - {v}' for v in sorted([
    'Japonica', 'Indica', 'Parboiled Rice', 'Brown Rice', 'Broken Rice',
    'Rice Flour Fine', 'Rice Brown Flour', 'Rice Precooked Flour',
    'Rice Gelatinized Flour', 'Pre-gelatinized Rice', 'Rice Semolina',
    'Rice Starch Native', 'Rice Starch Modified', 'Rice Protein Concentrate',
    'Rice Flour Baby Food Grade'
]))

wheat_varieties_list = '\n'.join(f'   - {v}' for v in sorted([
    'Wheat Soft Flour', 'Wheat Durum Flour', 'Wheat Semolina',
    'Wheat Bran', 'Wheat Germ', 'Wheat Whole Grain Flour',
    'Rye Flour', 'Barley Pearled'
]))

pulse_varieties_list = '\n'.join(f'   - {v}' for v in sorted([
    'Chickpea Flour', 'Red Lentil Flour', 'Green Lentil Flour',
    'Yellow Pea Flour', 'Green Pea Flour', 'Faba Bean Flour',
    'Pea Protein Isolate', 'Pulse Starch', 'Pulse Fiber', 'Toasted Pulse Flour'
]))

# Inyectar (SIN PLACEHOLDERS CONFLICTIVOS)
PROMPTS['entity_extraction_system_prompt'] = PROMPTS['entity_extraction_system_prompt'].format(
    entity_types=DACSA_ENTITY_TYPES.format(
        maize_varieties=maize_varieties_list,
        rice_varieties=rice_varieties_list,
        wheat_varieties=wheat_varieties_list,
        pulse_varieties=pulse_varieties_list,
        technology_keywords=', '.join(TECHNOLOGY_KEYWORDS),
        metric_whitelist='\n'.join(f'   - {m}' for m in sorted(METRIC_WHITELIST)),
        process_whitelist='\n'.join(f'   - {p}' for p in sorted(PROCESS_WHITELIST))
    )
)

print("\n" + "="*80)
print("✅ PROMPTS LOADED v1.5.0.1 (CHANNEL KEYERROR FIX)")
print("="*80)
print("🔧 FIX:")
print("   • Eliminados placeholders {market_channels} y {market_countries}")
print("   • Market channels/countries hardcodeados en definición")
print("   • 'Channel' → 'ChannelName' para evitar parser confusion")
print("="*80)
print(f"📊 Products: {len(PRODUCT_WHITELIST)} | Varieties: {len(VARIETY_WHITELIST)}")
print(f"📊 Metrics: {len(METRIC_WHITELIST)} | Processes: {len(PROCESS_WHITELIST)}")
print("="*80 + "\n")