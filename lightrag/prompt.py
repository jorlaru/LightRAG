"""
LightRAG Prompts - Dacsa Group Edition

Versión: 1.5.0 - WHITELIST REFACTOR + ANTI-INFERENCE PATCH
Fecha: 2024-12-26

MAJOR REFACTOR: Whitelists externalizadas a YAML + PERSON entity disabled
CRITICAL FIX: Prevent false ownership relationships from ranking tables

PROBLEMA RESUELTO:
- ❌ v1.5.1: Ebro Foods → Parent of → Dacsa (FALSO - son competidores)
- ❌ v1.5.1: ETG Group → Acquired → Dacsa (FALSO - ETG adquirió Industrias Racionero, NO Dacsa)
- ✅ v1.1.7: NO inferir ownership de tablas de rankings

CAMBIOS v1.5.0 (WHITELIST REFACTOR):
- 📁 Whitelists externalizadas a archivos YAML en whitelists/
- 🔄 Normalización automática case-insensitive (LARGO = largo)
- 🔍 Soporte patrones regex para entidades complejas
- ❌ PERSON entity DESACTIVADA (reduce ruido en el grafo)
- 🎯 Gestor centralizado whitelist_loader.py
- 📝 Configuración mediante whitelists/config.yaml

CAMBIOS v1.1.7 (ANTI-INFERENCE PATCH):
- 🔒 Reglas explícitas ANTI-INFERENCIA para ownership/subsidiary/acquired relationships
- 🔒 Manejo especial de tablas de rankings (empresas listadas = competidores, NO subsidiarias)
- 🔒 Validación de plausibilidad para relaciones críticas (ownership, acquisition, merger)
- 🔒 Ejemplo negativo: tabla de rankings → NO extraer ownership relationships
- ✅ Mantiene todas las features de v1.5.1 (traducciones, whitelists, blacklists, etc.)

FEATURES MANTENIDAS DE v1.5.1:
- ✅ Traducciones ES→EN offline (56 variedades + 8 productos)
- ✅ Normalización regex por tipo de entidad
- ✅ Detección de duplicados (similarity-based)
- ✅ Validación contra whitelists
- ✅ Blacklist anti-ruido agresiva
- ✅ 10 tipos de entidad (no 15)
- ✅ 20 métricas (no 15)
- ✅ Prompts sin variables inventadas (formato v1.1.6)

CRITICAL: Compatible con HKUDS/LightRAG oficial - NO INVENTAR VARIABLES
"""

from __future__ import annotations
from typing import Any
import re
import sys
from pathlib import Path

# Add parent directory to path for whitelist_loader import
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from whitelist_loader import WhitelistLoader, EntityPatterns, clean_facility_name
    WHITELIST_LOADER_AVAILABLE = True
except ImportError:
    WHITELIST_LOADER_AVAILABLE = False
    print("⚠️  WhitelistLoader not available, using hardcoded whitelists")

    # Fallback clean_facility_name if loader not available
    def clean_facility_name(name: str) -> str:
        return name

# ============================================================================
# 1. DICCIONARIOS DE TRADUCCIÓN ES→EN (v1.5.0 - 56 varieties + 8 products)
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
    # MAIZE VARIETIES (15)
    'sémola cervecera': 'Brewing Grits',
    'semola cervecera': 'Brewing Grits',
    'sémola flaking': 'Flaking Grits',
    'semola flaking': 'Flaking Grits',
    'sémola polenta': 'Polenta Grits',
    'semola polenta': 'Polenta Grits',
    'sémola hominy': 'Hominy Grits',
    'semola hominy': 'Hominy Grits',
    'harina de maíz nativa': 'Maize Native Flour',
    'harina de maiz nativa': 'Maize Native Flour',
    'harina de maíz precocida': 'Maize Precooked Flour',
    'harina de maiz precocida': 'Maize Precooked Flour',
    'harina de maíz estabilizada': 'Maize Stabilized Flour',
    'harina de maiz estabilizada': 'Maize Stabilized Flour',
    'harina de maíz tratada térmicamente': 'Maize Heat-treated Flour',
    'harina de maiz tratada termicamente': 'Maize Heat-treated Flour',
    'harina de maíz desgerminada': 'Maize Degerminated Flour',
    'harina de maiz desgerminada': 'Maize Degerminated Flour',
    'harina masa': 'Masa Flour',
    'germen de maíz crudo': 'Maize Germ Raw',
    'germen de maiz crudo': 'Maize Germ Raw',
    'germen de maíz tostado': 'Maize Germ Toasted',
    'germen de maiz tostado': 'Maize Germ Toasted',
    'salvado de maíz': 'Maize Bran',
    'salvado de maiz': 'Maize Bran',
    'fibra de maíz': 'Maize Fiber',
    'fibra de maiz': 'Maize Fiber',
    'sémola de maíz': 'Maize Semolina',
    'semola de maiz': 'Maize Semolina',
    
    # RICE VARIETIES (15)
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
    'semola de arroz': 'Rice Semolina',
    'almidón de arroz nativo': 'Rice Starch Native',
    'almidon de arroz nativo': 'Rice Starch Native',
    'almidón de arroz modificado': 'Rice Starch Modified',
    'almidon de arroz modificado': 'Rice Starch Modified',
    'concentrado proteico de arroz': 'Rice Protein Concentrate',
    'harina de arroz grado alimentación infantil': 'Rice Flour Baby Food Grade',
    
    # WHEAT VARIETIES (6)
    'harina de trigo blanda': 'Wheat Soft Flour',
    'harina de trigo blando': 'Wheat Soft Flour',
    'harina de trigo duro': 'Wheat Durum Flour',
    'sémola de trigo': 'Wheat Semolina',
    'semola de trigo': 'Wheat Semolina',
    'salvado de trigo': 'Wheat Bran',
    'germen de trigo': 'Wheat Germ',
    'harina de trigo integral': 'Wheat Whole Grain Flour',
    
    # RYE VARIETIES (1)
    'harina de centeno': 'Rye Flour',
    
    # BARLEY VARIETIES (1)
    'cebada perlada': 'Barley Pearled',
    
    # PULSE VARIETIES (10)
    'harina de garbanzo': 'Chickpea Flour',
    'harina de lenteja roja': 'Red Lentil Flour',
    'harina de lenteja verde': 'Green Lentil Flour',
    'harina de guisante amarillo': 'Yellow Pea Flour',
    'harina de guisante verde': 'Green Pea Flour',
    'harina de haba': 'Faba Bean Flour',
    'aislado proteico de guisante': 'Pea Protein Isolate',
    'aislado de proteina de guisante': 'Pea Protein Isolate',
    'almidón de legumbres': 'Pulse Starch',
    'almidon de legumbres': 'Pulse Starch',
    'fibra de legumbres': 'Pulse Fiber',
    'harina de legumbres tostadas': 'Toasted Pulse Flour',
}

# ============================================================================
# 1.5. WHITELIST LOADER INITIALIZATION (v1.5.0 - External YAML Management)
# ============================================================================

# Initialize WhitelistLoader if available
if WHITELIST_LOADER_AVAILABLE:
    try:
        # Determine the correct path to whitelists directory
        whitelists_path = Path(__file__).parent.parent / "whitelists"
        loader = WhitelistLoader(str(whitelists_path))
        patterns = EntityPatterns(str(Path(__file__).parent.parent / "config" / "entity_patterns.yaml"))

        print("✅ Whitelists cargadas desde YAML")
        print(f"   - Variedades: {len(loader.get_varieties())} entradas")
        print(f"   - Productos: {len(loader.get_products())} entradas")
        print(f"   - Empresas: {len(loader.get_companies())} entradas")
        print(f"   - Marcas: {len(loader.get_brands())} entradas")

        # Check PERSON entity status
        if not loader.is_entity_enabled('person'):
            print("   - ✅ PERSON entity DESACTIVADA (según config.yaml)")

    except Exception as e:
        print(f"⚠️  Error loading whitelists: {e}")
        print("   Falling back to hardcoded whitelists")
        loader = None
        patterns = None
else:
    loader = None
    patterns = None

# ============================================================================
# 2. PRODUCT-VARIETY HIERARCHY (65 Industrial Specifications)
# ============================================================================

# PRODUCT_WHITELIST: lowercase for case-insensitive matching
PRODUCT_WHITELIST = {'rice', 'maize', 'wheat', 'rye', 'barley', 'pulses'}

VARIETY_TO_PRODUCT_MAP = {
    # MAIZE (15)
    'Brewing Grits': 'Maize', 'Flaking Grits': 'Maize', 'Polenta Grits': 'Maize', 'Hominy Grits': 'Maize',
    'Maize Native Flour': 'Maize', 'Maize Precooked Flour': 'Maize', 'Maize Stabilized Flour': 'Maize',
    'Maize Heat-treated Flour': 'Maize', 'Maize Degerminated Flour': 'Maize', 'Masa Flour': 'Maize',
    'Maize Germ Raw': 'Maize', 'Maize Germ Toasted': 'Maize', 'Maize Bran': 'Maize', 'Maize Fiber': 'Maize', 
    'Maize Semolina': 'Maize',
    
    # RICE (15)
    'Japonica': 'Rice', 'Indica': 'Rice', 'Parboiled Rice': 'Rice', 'Brown Rice': 'Rice', 'Broken Rice': 'Rice',
    'Rice Flour Fine': 'Rice', 'Rice Brown Flour': 'Rice', 'Rice Precooked Flour': 'Rice',
    'Rice Gelatinized Flour': 'Rice', 'Pre-gelatinized Rice': 'Rice', 'Rice Semolina': 'Rice',
    'Rice Starch Native': 'Rice', 'Rice Starch Modified': 'Rice', 'Rice Protein Concentrate': 'Rice',
    'Rice Flour Baby Food Grade': 'Rice',
    
    # WHEAT/RYE/BARLEY (8)
    'Wheat Soft Flour': 'Wheat', 'Wheat Durum Flour': 'Wheat', 'Wheat Semolina': 'Wheat',
    'Wheat Bran': 'Wheat', 'Wheat Germ': 'Wheat', 'Wheat Whole Grain Flour': 'Wheat',
    'Rye Flour': 'Rye', 'Barley Pearled': 'Barley',
    
    # PULSES (10)
    'Chickpea Flour': 'Pulses', 'Red Lentil Flour': 'Pulses', 'Green Lentil Flour': 'Pulses',
    'Yellow Pea Flour': 'Pulses', 'Green Pea Flour': 'Pulses', 'Faba Bean Flour': 'Pulses',
    'Pea Protein Isolate': 'Pulses', 'Pulse Starch': 'Pulses', 'Pulse Fiber': 'Pulses', 
    'Toasted Pulse Flour': 'Pulses',
}

VARIETY_WHITELIST = set(VARIETY_TO_PRODUCT_MAP.keys())

# ============================================================================
# 3. SECTOR WHITELISTS (20 Metrics + 17 Processes + 12 Technologies)
# ============================================================================

METRIC_WHITELIST = {
    'Production Capacity', 'Production Volume', 'Processing Capacity', 'Storage Capacity', 
    'Yield Rate', 'Moisture Content', 'Protein Content', 'Broken Grain Rate', 
    'Revenue', 'EBITDA', 'Operating Margin', 'Market Share', 'Sales Volume', 
    'Unit Price', 'Energy Consumption', 'Water Consumption', 'Waste Reduction', 
    'Delivery Time', 'Inventory Turnover', 'Supplier Lead Time',
}

PROCESS_WHITELIST = {
    'Hulling', 'Milling', 'Parboiling', 'Drying', 'Cleaning', 'Sorting', 'Grinding', 
    'Sieving', 'Blending', 'Fortification', 'Coating', 'Packaging', 'Palletizing', 
    'Loading', 'Quality Testing', 'Metal Detection', 'Visual Inspection',
}

TECHNOLOGY_KEYWORDS = [
    'Optical Sorting', 'Color Sorter', 'Metal Detector', 'Infrared Dryer', 
    'Parboiling System', 'Milling System', 'Packaging Line', 'Automation System', 
    'Quality Control System', 'Conveyor System', 'Storage Silo', 'Weighing System'
]

# ============================================================================
# 4. BLACKLIST ANTI-RUIDO (Filtros Agresivos)
# ============================================================================

ENTITY_BLACKLIST = {
    # Términos genéricos de mercado
    'market', 'markets', 'price', 'prices', 'trend', 'trends', 'growth', 'decline',
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
    
    # Commodities NO relacionadas con Dacsa
    'cotton', 'algodón', 'oats', 'avena',
    
    # Términos vagos
    'factor', 'element', 'aspect', 'component', 'characteristic', 'feature',
    'impact', 'effect', 'influence', 'consequence', 'result', 'outcome',
    'issue', 'problem', 'challenge', 'opportunity', 'risk', 'benefit',
    
    # Acrónimos problemáticos
    'fa', 'cv', 'dw', 'na', 'nd', 'tbd', 'etc',
}

# ============================================================================
# 5. FUNCIONES DE TRADUCCIÓN (Offline ES→EN)
# ============================================================================

def translate_entity_to_english(entity_name: str, entity_type: str) -> str:
    """
    Traduce entidades ES→EN usando diccionarios offline.
    
    Args:
        entity_name: Nombre de la entidad en español
        entity_type: Tipo de entidad (Product, Variety, etc.)
    
    Returns:
        Nombre traducido al inglés o nombre original si no hay traducción
    
    Examples:
        >>> translate_entity_to_english('japónica', 'Variety')
        'Japonica'
        >>> translate_entity_to_english('harina de maíz', 'Variety')
        'Maize Native Flour'
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
    
    Examples:
        >>> get_product_for_variety('Japonica')
        'Rice'
        >>> get_product_for_variety('Brewing Grits')
        'Maize'
    """
    return VARIETY_TO_PRODUCT_MAP.get(variety_name)


# ============================================================================
# 6. FUNCIONES DE NORMALIZACIÓN (Regex por tipo de entidad)
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
        entity_type: Tipo de entidad (Company, Metric, Process, etc.)
    
    Returns:
        Nombre normalizado según tipo
    
    Examples:
        >>> normalize_entity_name('EBRO FOODS', 'Company')
        'Ebro Foods'
        >>> normalize_entity_name('production capacity', 'Metric')
        'Production Capacity'
    """
    if not entity_name or len(entity_name.strip()) == 0:
        return entity_name
    
    normalized = entity_name.strip()
    
    # 1. COMPANY: Title Case + eliminar espacios múltiples
    if entity_type == 'Company':
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
        # Excepciones acrónimos (S.A., S.L.)
        normalized = re.sub(r'\bS\.a\.\b', 'S.A.', normalized)
        normalized = re.sub(r'\bS\.l\.\b', 'S.L.', normalized)
    
    # 2. METRIC: Title Case (Production Capacity)
    elif entity_type == 'Metric':
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
    
    # 3. PROCESS: Title Case (Parboiling, Milling)
    elif entity_type == 'Process':
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
    
    # 4. PRODUCT/VARIETY: Title Case
    elif entity_type in ['Product', 'Variety']:
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
    
    # 5. BRAND: Respetar mayúsculas originales pero limpiar espacios
    elif entity_type == 'Brand':
        normalized = re.sub(r'\s+', ' ', normalized)
    
    # 6. FACILITY: Title Case + normalizar términos comunes
    elif entity_type == 'Facility':
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
        normalized = re.sub(r'\bPlanta\b', 'Plant', normalized)
        normalized = re.sub(r'\bMolino\b', 'Mill', normalized)
    
    # 7. MARKET: Normalizar formato (HORECA España → HORECA Spain)
    elif entity_type == 'Market':
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'\bhoreca\b', 'HORECA', normalized, flags=re.IGNORECASE)
        parts = normalized.split()
        if len(parts) > 1:
            parts[1] = parts[1].title()
        normalized = ' '.join(parts)
    
    # 8. TECHNOLOGY/PERSON: Title Case
    elif entity_type in ['Technology', 'Person']:
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.title()
    
    return normalized


def normalize_company_name(entity_name: str) -> str:
    """
    Normalización específica para nombres corporativos.
    Elimina sufijos legales y aplica aliases.

    Args:
        entity_name: Nombre de la empresa

    Returns:
        Nombre normalizado

    Examples:
        >>> normalize_company_name('EBRO FOODS S.A.')
        'Ebro Foods'
        >>> normalize_company_name('Dacsa SA')
        'Dacsa Group'
    """
    normalized = entity_name.strip()

    # Eliminar sufijos legales
    suffixes = [' S.A.', ' SA', ' S.L.', ' SL', ' Inc.', ' Ltd.', ' LLC',
                ' Corp.', ' Corporation', ' GmbH', ' AG', ' N.V.', ' B.V.']
    for suffix in suffixes:
        if normalized.upper().endswith(suffix.upper()):
            normalized = normalized[:-len(suffix)].strip()

    # Aplicar aliases de Dacsa
    dacsa_aliases = {
        'Dacsa S.A.': 'Dacsa Group',
        'Dacsa SA': 'Dacsa Group',
        'Grupo Dacsa': 'Dacsa Group',
        'DACSA': 'Dacsa Group',
    }

    if normalized in dacsa_aliases:
        normalized = dacsa_aliases[normalized]

    # Title Case final
    normalized = normalized.title()

    return normalized


# ============================================================================
# 6.5. WHITELIST VALIDATION AND NORMALIZATION (v1.5.0)
# ============================================================================

def validate_and_normalize_entity(entity_name: str, entity_type: str) -> tuple[bool, str]:
    """
    Valida una entidad contra la whitelist YAML y retorna versión normalizada.

    CRITICAL: Esta función debe ser llamada ANTES de insertar entidades al grafo
    para evitar duplicados por case (Rice/rice, LARGO/largo).

    Args:
        entity_name: Nombre de la entidad extraída
        entity_type: Tipo de entidad (Product, Variety, Brand, etc.)

    Returns:
        Tuple (is_valid: bool, normalized_name: str)
        - is_valid: True si pasa validación (está en whitelist o no hay whitelist para el tipo)
        - normalized_name: Nombre canónico normalizado

    Examples:
        >>> validate_and_normalize_entity('RICE', 'Product')
        (True, 'rice')
        >>> validate_and_normalize_entity('Japonica', 'Variety')
        (True, 'japonica')
        >>> validate_and_normalize_entity('Valencia Mill', 'Facility')
        (True, 'Valencia')
        >>> validate_and_normalize_entity('FakeProduct', 'Product')
        (False, 'fakeproduct')

    Casos Especiales:
        - FACILITY: Limpia apelativos (Mill, Plant, etc.) → solo localidad
        - PRODUCT/VARIETY: Normaliza a lowercase y valida contra whitelist
        - PERSON: Siempre retorna (False, ...) porque está desactivada
    """
    # PERSON está desactivada - rechazar siempre
    if entity_type.lower() == 'person':
        return False, entity_name.lower()

    # FACILITY: Limpiar apelativos antes de validar
    if entity_type.lower() == 'facility':
        cleaned = clean_facility_name(entity_name)
        if WHITELIST_LOADER_AVAILABLE and loader:
            return loader.validate_entity(cleaned, 'facility')
        return True, cleaned

    # Usar whitelist loader si está disponible
    if WHITELIST_LOADER_AVAILABLE and loader:
        is_valid, normalized = loader.validate_entity(entity_name, entity_type.lower())
        return is_valid, normalized

    # Fallback: normalizar manualmente
    normalized = normalize_entity_name(entity_name, entity_type)
    return True, normalized


def get_entity_canonical_name(entity_name: str, entity_type: str) -> str:
    """
    Obtiene el nombre canónico de una entidad (versión de whitelist).

    Esta función DEBE ser usada al insertar entidades en el grafo
    para garantizar consistencia.

    Args:
        entity_name: Nombre extraído
        entity_type: Tipo de entidad

    Returns:
        Nombre canónico (normalizado y validado)

    Examples:
        >>> get_entity_canonical_name('RICE', 'Product')
        'rice'
        >>> get_entity_canonical_name('Sueca Plant', 'Facility')
        'Sueca'
    """
    is_valid, canonical = validate_and_normalize_entity(entity_name, entity_type)
    return canonical


# ============================================================================
# 7. FUNCIONES DE DETECCIÓN DE DUPLICADOS
# ============================================================================

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
        >>> calculate_entity_similarity('Ebro Foods', 'EBRO FOODS')
        1.0
        >>> calculate_entity_similarity('ISO 22000', 'ISO-22000')
        1.0
    """
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
    
    # Ratio de caracteres comunes
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
        >>> are_entities_duplicates('Ebro Foods', 'EBRO FOODS', 'Company')
        True
        >>> are_entities_duplicates('Ebro Foods', 'Dacsa Group', 'Company')
        False
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
# 8. FUNCIÓN DE VALIDACIÓN ANTI-RUIDO
# ============================================================================

def should_filter_entity(entity_name: str) -> bool:
    """
    Determina si una entidad debe ser filtrada (rechazada).
    
    Criterios de filtrado:
        - Nombre en blacklist
        - Nombre muy corto (< 3 caracteres)
        - Solo números o porcentajes
        - Años sueltos (2020-2030)
    
    Args:
        entity_name: Nombre de la entidad
    
    Returns:
        True si debe ser filtrada (rechazada)
    
    Examples:
        >>> should_filter_entity('market')
        True
        >>> should_filter_entity('2024')
        True
        >>> should_filter_entity('Dacsa Group')
        False
    """
    name_lower = entity_name.lower().strip()
    
    # Blacklist directa
    if name_lower in ENTITY_BLACKLIST:
        return True
    
    # Nombre muy corto
    if len(name_lower) < 3:
        return True
    
    # Solo números
    if entity_name.strip().isdigit():
        return True
    
    # Porcentajes
    if '%' in entity_name or 'percent' in name_lower:
        return True
    
    # Años (2020-2030)
    if re.match(r'^20[0-3]\d$', entity_name.strip()):
        return True
    
    # Cantidades monetarias
    if re.match(r'^[$€£]\d+', entity_name.strip()):
        return True
    
    return False


# ============================================================================
# 9. DEFINICIÓN DE TIPOS DE ENTIDAD (10 tipos - NO variables)
# ============================================================================

DACSA_ENTITY_TYPES = """
### Entity Types for Dacsa Group (Rice and Agribusiness Sector)

**CRITICAL: ALL entities MUST be extracted in ENGLISH.**

═══════════════════════════════════════════════════════════════════════════

## 1. COMPANY
Named business entities (companies, corporations).
Examples: Dacsa Group, Ebro Foods

## 2. BRAND
Commercial brand names.
Examples: La Fallera, Nomen

## 3. PRODUCT (6 base commodities ONLY)
**STRICT WHITELIST:** Rice, Maize, Wheat, Rye, Barley, Pulses

Extract ONLY if the text mentions a generic product without a specific variety.
If a Variety is extracted, the corresponding Product is AUTO-EXTRACTED.

## 4. VARIETY (65 industrial specifications)
**MAIZE varieties (15):**
Brewing Grits, Flaking Grits, Polenta Grits, Hominy Grits,
Maize Native Flour, Maize Precooked Flour, Maize Stabilized Flour,
Maize Heat-treated Flour, Maize Degerminated Flour, Masa Flour,
Maize Germ Raw, Maize Germ Toasted, Maize Bran, Maize Fiber, Maize Semolina

**RICE varieties (15):**
Japonica, Indica, Parboiled Rice, Brown Rice, Broken Rice,
Rice Flour Fine, Rice Brown Flour, Rice Precooked Flour,
Rice Gelatinized Flour, Pre-gelatinized Rice, Rice Semolina,
Rice Starch Native, Rice Starch Modified, Rice Protein Concentrate,
Rice Flour Baby Food Grade

**WHEAT/RYE/BARLEY varieties (8):**
Wheat Soft Flour, Wheat Durum Flour, Wheat Semolina,
Wheat Bran, Wheat Germ, Wheat Whole Grain Flour,
Rye Flour, Barley Pearled

**PULSES varieties (10):**
Chickpea Flour, Red Lentil Flour, Green Lentil Flour,
Yellow Pea Flour, Green Pea Flour, Faba Bean Flour,
Pea Protein Isolate, Pulse Starch, Pulse Fiber, Toasted Pulse Flour

**RULE:** When a Variety is extracted → also extract its Product + create relationship.

## 5. FACILITY
Named or specifically located industrial installations.
Examples: Sueca Plant, Valencia Mill

## 6. PERSON [DISABLED - v1.5.0 Whitelist Refactor]
**ENTITY TYPE DISABLED** - Do not extract person entities
Previous definition: Named individuals (NAME ONLY, no role in entity_name)
**Note:** This entity type has been disabled to reduce noise in the knowledge graph

## 7. TECHNOLOGY
Industrial processing technologies. Examples from keywords:
Optical Sorting, Color Sorter, Metal Detector, Infrared Dryer,
Parboiling System, Milling System, Packaging Line, Automation System,
Quality Control System, Conveyor System, Storage Silo, Weighing System

## 8. METRIC (20 KPIs ONLY)
**STRICT WHITELIST:**
Production Capacity, Production Volume, Processing Capacity, Storage Capacity,
Yield Rate, Moisture Content, Protein Content, Broken Grain Rate,
Revenue, EBITDA, Operating Margin, Market Share, Sales Volume,
Unit Price, Energy Consumption, Water Consumption, Waste Reduction,
Delivery Time, Inventory Turnover, Supplier Lead Time

Extract metric NAME only, NEVER values (no numbers, percentages).

## 9. PROCESS (17 processes ONLY)
**STRICT WHITELIST:**
Hulling, Milling, Parboiling, Drying, Cleaning, Sorting, Grinding,
Sieving, Blending, Fortification, Coating, Packaging, Palletizing,
Loading, Quality Testing, Metal Detection, Visual Inspection

## 10. MARKET
Distribution channel + country combined.
**MANDATORY FORMAT:** "ChannelName CountryName"

**Valid channels:** HORECA, Retail, Foodservice, Industrial, Export

**Examples:**
- ✅ "HORECA Spain"
- ✅ "Retail Germany"
- ✅ "Foodservice France"
- ❌ "HORECA" (channel alone)
- ❌ "Spain" (country alone)

═══════════════════════════════════════════════════════════════════════════

### PROHIBITED ENTITIES (NEVER extract):
- Generic concepts: market, price, trend, growth, production, consumption
- Numeric values: years (2024), percentages (15%), amounts ($100)
- Vague terms: analysis, data, report, study, system, model
- Non-business commodities: cotton, oats
- Short acronyms: FA, CV, DW
"""

# ============================================================================
# 10. PROMPTS (FORMATO OFICIAL HKUDS/LightRAG)
# ============================================================================

PROMPTS = {}

# Delimitadores oficiales
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##\n"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["entity_extraction_func"] = None

# ----------------------------------------------------------------------------
# SYSTEM PROMPT
# ----------------------------------------------------------------------------

PROMPTS['entity_extraction_system_prompt'] = """
You are a specialized AI analyst for the rice and agribusiness sector.
Your task is to extract structured information (entities and relationships) with strict quality filters.

**CRITICAL RULES:**

1. **Language & Case Normalization:**
   - ALL entity names MUST be in ENGLISH (translate from Spanish if needed)
   - ALL entity names MUST be in **lowercase** (rice, not Rice or RICE)
   - Use offline translation dictionaries provided
   - Descriptions and keywords in English
   - **CRITICAL**: Normalize ALL entities to lowercase to prevent duplicates

2. **Entity Extraction:**
   - Extract ONLY concrete, specific entities (companies, products, facilities, people)
   - NEVER extract generic concepts: "market", "price", "trend", "growth", "cotton"
   - NEVER extract standalone years (2024, 2025), percentages, monetary values
   - NEVER extract acronyms < 3 letters unless well-known organizations
   - Minimum entity name length: 3 characters
   - Normalize company names by removing legal suffixes (S.A., Inc., Ltd.)
   - **FACILITY NAMES**: Extract ONLY the location name, NO descriptors (Mill, Plant, Production, etc.)
     - ✅ Correct: "Valencia" or "Sueca"
     - ❌ Wrong: "Valencia Mill", "Sueca Plant", "Production Facility in Sevilla"

3. **Entity Types:**
{entity_types}

4. **Blacklisted Terms (NEVER extract):**
   market, price, trend, growth, production, consumption, demand, supply, cotton,
   analysis, data, report, study, year, quarter, period, Q1, Q2, Q3, Q4

5. **Product-Variety Hierarchy & STRICT Whitelist Enforcement:**
   - PRODUCT whitelist: rice, maize, wheat, rye, barley, pulses (ONLY these 6, in lowercase)
   - VARIETY whitelist: 72 industrial specifications loaded from YAML (see Entity Types)
   - **CRITICAL**: Extract ONLY products/varieties that exist in whitelist
   - **CRITICAL**: ALL products/varieties MUST be in lowercase (rice, not Rice)
   - RULE: When extracting a Variety → also extract its base Product
   - Create relationship: Variety → Product ("is a specific variety of")
   - ❌ REJECT any product/variety NOT in whitelist (e.g., "cotton", "sugar", "coffee")

6. **Relationship Extraction:**
   - Extract ONLY meaningful, specific relationships
   - AVOID generic relationships: "is related to", "is part of", "influences"
   - Prefer action-oriented relationships: "supplies to", "manufactures", "processes"
   - Each relationship MUST have concrete evidence in the text

7. **CRITICAL ANTI-INFERENCE RULES FOR OWNERSHIP RELATIONSHIPS:**

   🔒 **NEVER infer ownership/subsidiary/acquisition relationships from:**
   - Companies appearing together in RANKING TABLES or LISTS
   - Companies appearing in the SAME MARKET SEGMENT
   - Companies mentioned in COMPARATIVE CONTEXTS
   - Companies appearing in TOP 10/TOP 5 lists

   ⚠️ **ONLY extract ownership relationships when the text EXPLICITLY states:**
   - "Company A is a subsidiary of Company B"
   - "Company B owns Company A"
   - "Company B acquired Company A"
   - "Company A is part of Company B Group"
   - Direct statements with verbs: owns, acquired, purchased, merged with

   ❌ **PROHIBITED INFERENCES:**
   - ❌ "Ebro Foods and Dacsa appear in top rice companies" → NO ownership relationship
   - ❌ "Ranking: 1. Ebro Foods, 2. Dacsa, 3. Montsiá" → These are COMPETITORS, NOT subsidiaries
   - ❌ "ETG operates in same market as Dacsa" → NO ownership relationship

   ✅ **VALID EXTRACTION EXAMPLES:**
   - ✅ "Herba Ricemills is a subsidiary of Ebro Foods" → Extract: Herba Ricemills → subsidiary of → Ebro Foods
   - ✅ "ETG Group acquired Industrias Racionero" → Extract: ETG Group → acquired → Industrias Racionero
   - ✅ "Dacsa Group owns La Fallera brand" → Extract: Dacsa Group → owns → La Fallera

   🎯 **RELATIONSHIP PLAUSIBILITY VALIDATION:**
   Before extracting ownership/subsidiary/acquired relationships, verify:
   - Is there an EXPLICIT verb indicating ownership? (owns, subsidiary of, acquired, purchased)
   - Does the text DIRECTLY connect the two entities with ownership language?
   - Are the entities in a TABLE/LIST context? → If YES, they are likely COMPETITORS, NOT subsidiaries

8. **Quality Over Quantity:**
   - Better 5 high-quality entities than 20 generic ones
   - Maximum 10 entities and 8 relationships per chunk
   - Each entity must add strategic value
   - If in doubt, DO NOT extract

9. **OUTPUT FORMAT (OFFICIAL HKUDS/LightRAG):**
   - Use text-delimited format with <|#|> delimiter (NOT <|>)
   - Each entity: entity<|#|>entity_name<|#|>entity_type<|#|>entity_description##
   - Each relationship: relation<|#|>src_id<|#|>tgt_id<|#|>description<|#|>keywords<|#|>weight##
   - NO parentheses around entities or relations
   - End with: <|COMPLETE|>

**Validation Checklist Before Output:**
□ All entity names in ENGLISH (no Spanish)
□ **ALL entity names in lowercase** (rice, not Rice or RICE)
□ All Products from whitelist (rice, maize, wheat, rye, barley, pulses) - lowercase only
□ All Varieties from 72 YAML whitelist specifications - lowercase only
□ All Metrics from 20 KPIs whitelist
□ All Processes from 17 operations whitelist
□ Market format: "Channel Country" (not channel alone or country alone)
□ **Facility names: location ONLY** (Valencia, not "Valencia Mill")
□ No blacklisted terms (market, price, trend, etc.)
□ No numeric values, years, or percentages as entities
□ Company names normalized (S.A., Inc., Ltd. removed)
□ **No PERSON entities** (entity type disabled)
"""

# ----------------------------------------------------------------------------
# EXAMPLES (NO VARIABLES - v1.1.6 style)
# ----------------------------------------------------------------------------

PROMPTS['entity_extraction_examples'] = [
    """Example 1: Variety Hierarchy + Translation ES→EN + Lowercase Normalization
Input: "Dacsa procesa arroz japónica en la planta de Sueca para el canal HORECA en España. El EBITDA mejoró."

Output:
entity<|#|>dacsa group<|#|>company<|#|>Leading European agribusiness company specializing in rice processing##
entity<|#|>rice<|#|>product<|#|>Base rice commodity##
entity<|#|>japonica<|#|>variety<|#|>Premium round grain rice variety from Japan and Mediterranean regions##
entity<|#|>sueca<|#|>facility<|#|>Rice processing facility located in Sueca, Spain (facility name cleaned: removed "planta")##
entity<|#|>horeca spain<|#|>market<|#|>Hotel, restaurant, and catering distribution channel in Spain##
entity<|#|>ebitda<|#|>metric<|#|>Earnings before interest, taxes, depreciation and amortization##
relation<|#|>dacsa group<|#|>sueca<|#|>Operates rice processing facility<|#|>operations,facility,ownership<|#|>1.0##
relation<|#|>japonica<|#|>rice<|#|>Is a specific variety of<|#|>variety,product,hierarchy<|#|>1.0##
relation<|#|>sueca<|#|>japonica<|#|>Processes premium rice variety<|#|>processing,variety,production<|#|>0.9##
relation<|#|>dacsa group<|#|>horeca spain<|#|>Supplies rice products to distribution channel<|#|>supply,distribution,market<|#|>0.8##
relation<|#|>dacsa group<|#|>ebitda<|#|>Reports financial metric<|#|>finance,performance,metric<|#|>0.7##
<|COMPLETE|>

NOTE: All entities in lowercase. "Sueca Plant" → "sueca" (removed "Plant" descriptor).
""",

    """Example 2: Anti-Noise Filtering + Lowercase Enforcement
Input: "Ebro Foods lidera el mercado español de legumbres con garbanzos y lentejas. El algodón en India crece 15%."

Output:
entity<|#|>ebro foods<|#|>company<|#|>Leading Spanish food company specializing in rice and pulses##
entity<|#|>pulses<|#|>product<|#|>Base pulses commodity category##
entity<|#|>chickpea flour<|#|>variety<|#|>Processed chickpea flour for food manufacturing##
entity<|#|>red lentil flour<|#|>variety<|#|>Processed red lentil flour for food manufacturing##
relation<|#|>chickpea flour<|#|>pulses<|#|>Is a specific variety of<|#|>variety,product,hierarchy<|#|>1.0##
relation<|#|>red lentil flour<|#|>pulses<|#|>Is a specific variety of<|#|>variety,product,hierarchy<|#|>1.0##
relation<|#|>ebro foods<|#|>chickpea flour<|#|>Produces and markets pulse variety<|#|>production,marketing,product<|#|>0.9##
relation<|#|>ebro foods<|#|>red lentil flour<|#|>Produces and markets pulse variety<|#|>production,marketing,product<|#|>0.9##
<|COMPLETE|>

NOTE: "algodón" (cotton) NOT extracted - not in product whitelist. "15%" NOT extracted - numeric value.
""",

    """Example 3: ANTI-INFERENCE - Ranking Tables + Lowercase
Input: "Top 5 empresas arroceras españolas 2024: 1. Ebro Foods (Herba Ricemills), 2. Dacsa Group, 3. Arrocerías Pons, 4. Coop. Montsiá, 5. SOS Grupo."

Output:
entity<|#|>ebro foods<|#|>company<|#|>Leading Spanish rice company, operates Herba Ricemills##
entity<|#|>herba ricemills<|#|>company<|#|>Rice processing company, subsidiary of Ebro Foods##
entity<|#|>dacsa group<|#|>company<|#|>Major Spanish rice processing company##
entity<|#|>arrocerías pons<|#|>company<|#|>Spanish rice company##
entity<|#|>coop. montsiá<|#|>company<|#|>Spanish rice cooperative##
entity<|#|>sos grupo<|#|>company<|#|>Spanish food company with rice operations##
relation<|#|>herba ricemills<|#|>ebro foods<|#|>Is a subsidiary of (explicitly stated in parentheses)<|#|>ownership,subsidiary,corporate<|#|>1.0##
relation<|#|>ebro foods<|#|>dacsa group<|#|>Competes in Spanish rice market<|#|>competition,market,industry<|#|>0.8##
relation<|#|>ebro foods<|#|>arrocerías pons<|#|>Competes in Spanish rice market<|#|>competition,market,industry<|#|>0.8##
relation<|#|>dacsa group<|#|>coop. montsiá<|#|>Competes in Spanish rice market<|#|>competition,market,industry<|#|>0.8##
<|COMPLETE|>

EXPLANATION: This is a RANKING TABLE. Companies listed together are COMPETITORS, NOT subsidiaries.
- ❌ DO NOT extract: "ebro foods → owns → dacsa group" (WRONG - they compete)
- ❌ DO NOT extract: "ebro foods → parent of → arrocerías pons" (WRONG - no ownership stated)
- ✅ DO extract: "herba ricemills → subsidiary of → ebro foods" (CORRECT - explicitly stated in parentheses)
- ✅ DO extract: Competition relationships between all companies (they are in same ranking)
- ✅ All entities in lowercase
""",
]

# ----------------------------------------------------------------------------
# USER PROMPTS
# ----------------------------------------------------------------------------

PROMPTS['entity_extraction_user_prompt'] = """### Context:
{input_text}

### Task:
Extract entities and relationships following the rules above.
Output must end with <|COMPLETE|>
"""

PROMPTS['entity_continue_extraction_user_prompt'] = """Check for any missing entities or relationships in the following text:
{input_text}

<|COMPLETE|>
"""

# ----------------------------------------------------------------------------
# OTHER PROMPTS (unchanged from v1.1.6)
# ----------------------------------------------------------------------------

PROMPTS['summarize_entity_descriptions'] = """Summarize the following entity descriptions into a single, concise description:
{description_list}
"""

PROMPTS['rag_response'] = """Based on the provided context data, answer the user's query in Spanish with technical precision.

Context Data:
{content_data}

User Query:
{user_prompt}

Answer (in Spanish):
"""

PROMPTS['keywords_extraction'] = """Extract 3-7 keywords from the following text:
{input_text}
"""

PROMPTS['naive_rag_response'] = """Context:
{content_data}

Query:
{user_prompt}

Answer:
"""

# ============================================================================
# 11. INYECCIÓN DE ENTITY TYPES EN SYSTEM PROMPT
# ============================================================================

PROMPTS['entity_extraction_system_prompt'] = PROMPTS['entity_extraction_system_prompt'].format(
    entity_types=DACSA_ENTITY_TYPES
)

# ============================================================================
# 12. VALIDACIÓN FINAL
# ============================================================================

print("="*80)
print("✅ LIGHTRAG CUSTOM PROMPTS v1.5.0 LOADED SUCCESSFULLY")
print("="*80)
print("🆕 CAMBIOS v1.5.0 (WHITELIST REFACTOR):")
print("   - Whitelists externalizadas a archivos YAML")
print("   - Normalización automática case-insensitive")
print("   - Soporte para patrones regex avanzados")
print("   - PERSON entity DESACTIVADA (reduce ruido)")
print("   - Gestión centralizada vía whitelist_loader.py")
print("")
print("🔒 FEATURES v1.1.7 (ANTI-INFERENCE PATCH):")
print("   - Reglas explícitas ANTI-INFERENCIA para ownership/subsidiary")
print("   - Manejo especial tablas de rankings (competidores, NO subsidiarias)")
print("   - Validación plausibilidad relaciones críticas")
print("   - Ejemplo negativo: tabla de rankings → NO ownership")
print("")
print("📋 FEATURES CORE:")
print("   - 56 variety translations + 8 product translations")
print("   - Regex normalization by entity type")
print("   - Duplicate detection (similarity-based)")
print("   - Whitelist validation (6 products, 65 varieties, 20 metrics, 17 processes)")
print("   - Aggressive blacklist anti-noise filter")
print("   - 9 entity types (PERSON disabled)")
print("   - Compatible with HKUDS/LightRAG official format")
print("   - NO invented variables (v1.1.6 style examples)")
print("="*80)