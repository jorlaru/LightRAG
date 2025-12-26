# Refactorización LightRAG: Desacoplamiento Whitelists a YAML

## 📋 Resumen ejecutivo

**Objetivo**: Externalizar whitelists del `prompt.py` a archivos YAML gestionables como "base de datos", eliminando PERSON y añadiendo reglas regex.

**Impacto**:
- ✅ Whitelists editables sin tocar código
- ✅ Normalización case-insensitive automática
- ✅ Regex para patrones complejos (ARROZ + VARIEDAD)
- ✅ Eliminación de entidad PERSON
- ✅ Mantenimiento desacoplado y escalable

---

## 🏗️ Arquitectura propuesta

```
lightrag/
├── prompt.py                    # Lógica de extracción (sin whitelists hardcoded)
├── whitelist_loader.py          # Gestor centralizado de whitelists
├── whitelists/                  # 📁 Base de datos externa
│   ├── config.yaml              # Configuración general
│   ├── varieties.yaml           # Variedades de arroz
│   ├── products.yaml            # Productos (Arroz, Harina, etc.)
│   ├── brands.yaml              # Marcas comerciales
│   ├── companies.yaml           # Empresas
│   ├── facilities.yaml          # Instalaciones
│   ├── countries.yaml           # Países
│   ├── regions.yaml             # Regiones
│   ├── markets.yaml             # Mercados
│   ├── metrics.yaml             # Métricas
│   └── standards.yaml           # Estándares/Certificaciones
└── config/
    └── entity_patterns.yaml     # Reglas regex por entidad
```

---

## 📦 1. Estructura de archivos YAML

### `whitelists/config.yaml`
```yaml
# Configuración general de whitelists
version: "1.5.0"
case_sensitive: false  # Normalización automática a lowercase
enable_regex: true     # Activar patrones regex
merge_translations: true  # Fusionar español/inglés

# Entidades activas
enabled_entities:
  - variety
  - product
  - brand
  - company
  - facility
  - country
  - region
  - market
  - metric
  - standard
  # person: ELIMINADA (antes estaba activa)

# Entidades desactivadas
disabled_entities:
  - person  # Eliminada según requisito
  - organization  # Si quieres eliminar también
```

### `whitelists/varieties.yaml`
```yaml
# Variedades de arroz - Normalización español/inglés
# Formato: primary_name: [alias1, alias2, ...]

varieties:
  # Grano largo
  largo:
    spanish: ["largo", "arroz largo", "grano largo"]
    english: ["long grain", "long-grain rice", "long grain rice"]
    
  # Grano redondo
  redondo:
    spanish: ["redondo", "arroz redondo", "grano redondo", "round"]
    english: ["round grain", "round-grain rice", "round rice"]
    
  # Bomba
  bomba:
    spanish: ["bomba", "arroz bomba"]
    english: ["bomba rice"]
    
  # Basmati
  basmati:
    spanish: ["basmati", "arroz basmati"]
    english: ["basmati rice"]
    
  # Vaporizado
  vaporizado:
    spanish: ["vaporizado", "arroz vaporizado"]
    english: ["parboiled", "parboiled rice"]
    
  # Integral
  integral:
    spanish: ["integral", "arroz integral"]
    english: ["brown", "brown rice"]
    
  # Japonica
  japonica:
    spanish: ["japonica"]
    english: ["japonica rice"]
    
  # Indica
  indica:
    spanish: ["indica"]
    english: ["indica rice"]
    
  # Risotto
  risotto:
    spanish: ["risotto", "arroz risotto", "exóticos risotto"]
    english: ["risotto rice"]
    
  # Thai/Jazmín
  thai:
    spanish: ["thai", "jazmín", "jazmin", "exóticos thai.jazmin"]
    english: ["thai rice", "jasmine", "jasmine rice"]
    
  # Sushi
  sushi:
    spanish: ["sushi", "arroz sushi", "exóticos sushi"]
    english: ["sushi rice"]
    
  # Salvaje
  salvaje:
    spanish: ["salvaje", "arroz salvaje", "exóticos salvaje"]
    english: ["wild rice"]
    
  # Rápido
  rapido:
    spanish: ["rápido", "rapido", "arroz rápido"]
    english: ["quick cooking", "instant rice"]
    
  # Biológico
  biologico:
    spanish: ["biológico", "biologico", "bio", "ecológico"]
    english: ["organic", "organic rice"]
    
  # Origen
  origen:
    spanish: ["origen", "denominación origen", "exóticos d.origen"]
    english: ["origin", "designation of origin"]
    
  # Kamalís (variedad específica)
  kamalis:
    spanish: ["kamális", "kamalis"]
    english: ["kamalis rice"]
    
  # Pre-gelatinizado
  pregelatinizado:
    spanish: ["pre-gelatinizado", "pregelatinizado"]
    english: ["pre-gelatinized rice"]

# AÑADIR AQUÍ las variedades que faltan en tu whitelist
# Ejemplo:
#  nueva_variedad:
#    spanish: ["nombre_es", "alias_es"]
#    english: ["name_en", "alias_en"]
```

### `whitelists/products.yaml`
```yaml
# Productos derivados del arroz

products:
  arroz:
    names: ["arroz", "rice"]
    category: "grain"
    
  harina:
    names: ["harina de arroz", "rice flour", "harina arroz fina", "rice flour fine"]
    category: "flour"
    
  semola:
    names: ["sémola de arroz", "rice semolina", "semola"]
    category: "semolina"
    
  proteina:
    names: ["concentrado proteína arroz", "rice protein concentrate"]
    category: "protein"
    
  almidon:
    names: 
      - "almidón de arroz nativo"
      - "rice starch native"
      - "almidón de arroz modificado"
      - "rice starch modified"
    category: "starch"
    
  harina_precocida:
    names: ["harina arroz precocida", "rice precooked flour"]
    category: "flour"
    
  harina_gelatinizada:
    names: ["harina arroz gelatinizada", "rice gelatinized flour"]
    category: "flour"
    
  harina_integral:
    names: ["harina arroz integral", "rice brown flour"]
    category: "flour"
    
  arroz_partido:
    names: ["arroz partido", "broken rice"]
    category: "grain"
    
  vasitos:
    names: ["vasitos de arroz", "rice cups"]
    category: "prepared"
    
  pasta:
    names: ["pasta de arroz", "rice pasta"]
    category: "pasta"
```

### `whitelists/brands.yaml`
```yaml
# Marcas comerciales de arroz

brands:
  dacsa:
    - "Nomen"
    - "Bayo"
    - "Segadors del Delta"
    
  coop_arrozua:
    - "Doña Ana"
    - "El Ruedo"
    
  pasamar:
    - "Embajador"
    - "Aguila Oro"
    
  # AÑADIR el resto de marcas que tienes en tu whitelist actual
```

### `whitelists/companies.yaml`
```yaml
# Empresas del sector arrocero

companies:
  spanish:
    - "Dacsa Group"
    - "COOP. ARROZÚA"
    - "P. ARNANDIS MARTÍNEZ, S.A."
    - "PASAMAR"
    - "Ebro Foods"
    - "SOS"
    - "Nomen"
    - "Herba"
    # AÑADIR el resto...
    
  international:
    - "Bühler"
    - "Satake"
    # AÑADIR el resto...
```

### `whitelists/facilities.yaml`
```yaml
# Instalaciones industriales

facilities:
  processing_plants:
    - "planta"
    - "fábrica"
    - "factoría"
    - "plant"
    - "factory"
    
  storage:
    - "almacén"
    - "warehouse"
    - "silo"
    
  headquarters:
    - "sede"
    - "headquarters"
    - "central"
```

### `whitelists/countries.yaml`
```yaml
# Países relevantes

countries:
  - "España"
  - "Italy"
  - "France"
  - "India"
  - "Thailand"
  - "Vietnam"
  - "USA"
  - "China"
  # AÑADIR el resto...
```

### `whitelists/regions.yaml`
```yaml
# Regiones geográficas

regions:
  spanish:
    - "Valencia"
    - "Andalucía"
    - "Delta del Ebro"
    - "Extremadura"
    - "Sevilla"
    - "Tarragona"
    
  international:
    - "Southeast Asia"
    - "California"
    - "Punjab"
```

### `whitelists/markets.yaml`
```yaml
# Mercados y canales de distribución

markets:
  - "retail"
  - "foodservice"
  - "industrial"
  - "export"
  - "domestic"
  - "horeca"
  - "gran distribución"
```

### `whitelists/metrics.yaml`
```yaml
# Métricas y KPIs

metrics:
  production:
    - "toneladas"
    - "tons"
    - "producción"
    - "production"
    - "capacidad"
    - "capacity"
    
  financial:
    - "ingresos"
    - "revenue"
    - "ventas"
    - "sales"
    - "facturación"
    - "turnover"
    - "margen"
    - "margin"
    - "EBITDA"
    
  quality:
    - "calidad"
    - "quality"
    - "certificación"
    - "certification"
```

### `whitelists/standards.yaml`
```yaml
# Estándares y certificaciones

standards:
  quality:
    - "ISO 9001"
    - "HACCP"
    - "BRC"
    - "IFS"
    - "GlobalGAP"
    
  sustainability:
    - "Organic"
    - "Bio"
    - "Rainforest Alliance"
    - "Fairtrade"
    
  food_safety:
    - "FDA"
    - "EFSA"
    - "AESAN"
```

---

## 🔧 2. Gestor de whitelists

### `whitelist_loader.py`
```python
"""
Gestor centralizado de whitelists externalizadas en YAML.
Carga, normaliza y proporciona acceso a las entidades permitidas.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Set, Optional
import re


class WhitelistLoader:
    """Carga y gestiona whitelists desde archivos YAML externos."""
    
    def __init__(self, whitelists_dir: str = "whitelists"):
        """
        Inicializa el loader.
        
        Args:
            whitelists_dir: Directorio raíz de las whitelists YAML
        """
        self.whitelists_dir = Path(whitelists_dir)
        self.config = self._load_config()
        self.case_sensitive = self.config.get('case_sensitive', False)
        self.enable_regex = self.config.get('enable_regex', True)
        self.merge_translations = self.config.get('merge_translations', True)
        
        # Caché de whitelists cargadas
        self._cache = {}
        
    def _load_config(self) -> Dict:
        """Carga configuración general."""
        config_path = self.whitelists_dir / "config.yaml"
        if not config_path.exists():
            return {
                'case_sensitive': False,
                'enable_regex': True,
                'merge_translations': True,
                'enabled_entities': []
            }
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _normalize(self, text: str) -> str:
        """Normaliza texto según configuración."""
        if not self.case_sensitive:
            return text.lower().strip()
        return text.strip()
    
    def _load_yaml(self, filename: str) -> Dict:
        """Carga archivo YAML individual."""
        filepath = self.whitelists_dir / filename
        if not filepath.exists():
            return {}
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def get_varieties(self) -> Set[str]:
        """
        Carga variedades de arroz con fusión español/inglés.
        
        Returns:
            Set normalizado de todas las variedades y aliases
        """
        if 'varieties' in self._cache:
            return self._cache['varieties']
        
        data = self._load_yaml('varieties.yaml')
        varieties = set()
        
        for variety_key, translations in data.get('varieties', {}).items():
            # Añadir nombre primario
            varieties.add(self._normalize(variety_key))
            
            if self.merge_translations:
                # Fusionar español e inglés
                for lang_key in ['spanish', 'english']:
                    if lang_key in translations:
                        for alias in translations[lang_key]:
                            varieties.add(self._normalize(alias))
            else:
                # Solo usar una lengua (configurable)
                primary_lang = self.config.get('primary_language', 'spanish')
                if primary_lang in translations:
                    for alias in translations[primary_lang]:
                        varieties.add(self._normalize(alias))
        
        self._cache['varieties'] = varieties
        return varieties
    
    def get_products(self) -> Set[str]:
        """Carga productos derivados del arroz."""
        if 'products' in self._cache:
            return self._cache['products']
        
        data = self._load_yaml('products.yaml')
        products = set()
        
        for product_data in data.get('products', {}).values():
            for name in product_data.get('names', []):
                products.add(self._normalize(name))
        
        self._cache['products'] = products
        return products
    
    def get_brands(self) -> Set[str]:
        """Carga marcas comerciales."""
        if 'brands' in self._cache:
            return self._cache['brands']
        
        data = self._load_yaml('brands.yaml')
        brands = set()
        
        for brand_list in data.get('brands', {}).values():
            for brand in brand_list:
                brands.add(self._normalize(brand))
        
        self._cache['brands'] = brands
        return brands
    
    def get_companies(self) -> Set[str]:
        """Carga empresas del sector."""
        if 'companies' in self._cache:
            return self._cache['companies']
        
        data = self._load_yaml('companies.yaml')
        companies = set()
        
        for company_list in data.get('companies', {}).values():
            for company in company_list:
                companies.add(self._normalize(company))
        
        self._cache['companies'] = companies
        return companies
    
    def get_facilities(self) -> Set[str]:
        """Carga instalaciones."""
        if 'facilities' in self._cache:
            return self._cache['facilities']
        
        data = self._load_yaml('facilities.yaml')
        facilities = set()
        
        for facility_list in data.get('facilities', {}).values():
            for facility in facility_list:
                facilities.add(self._normalize(facility))
        
        self._cache['facilities'] = facilities
        return facilities
    
    def get_countries(self) -> Set[str]:
        """Carga países."""
        if 'countries' in self._cache:
            return self._cache['countries']
        
        data = self._load_yaml('countries.yaml')
        countries = set()
        
        for country in data.get('countries', []):
            countries.add(self._normalize(country))
        
        self._cache['countries'] = countries
        return countries
    
    def get_regions(self) -> Set[str]:
        """Carga regiones geográficas."""
        if 'regions' in self._cache:
            return self._cache['regions']
        
        data = self._load_yaml('regions.yaml')
        regions = set()
        
        for region_list in data.get('regions', {}).values():
            for region in region_list:
                regions.add(self._normalize(region))
        
        self._cache['regions'] = regions
        return regions
    
    def get_markets(self) -> Set[str]:
        """Carga mercados y canales."""
        if 'markets' in self._cache:
            return self._cache['markets']
        
        data = self._load_yaml('markets.yaml')
        markets = {self._normalize(m) for m in data.get('markets', [])}
        
        self._cache['markets'] = markets
        return markets
    
    def get_metrics(self) -> Set[str]:
        """Carga métricas y KPIs."""
        if 'metrics' in self._cache:
            return self._cache['metrics']
        
        data = self._load_yaml('metrics.yaml')
        metrics = set()
        
        for metric_list in data.get('metrics', {}).values():
            for metric in metric_list:
                metrics.add(self._normalize(metric))
        
        self._cache['metrics'] = metrics
        return metrics
    
    def get_standards(self) -> Set[str]:
        """Carga estándares y certificaciones."""
        if 'standards' in self._cache:
            return self._cache['standards']
        
        data = self._load_yaml('standards.yaml')
        standards = set()
        
        for standard_list in data.get('standards', {}).values():
            for standard in standard_list:
                standards.add(self._normalize(standard))
        
        self._cache['standards'] = standards
        return standards
    
    def get_all_whitelists(self) -> Dict[str, Set[str]]:
        """
        Carga todas las whitelists activas.
        
        Returns:
            Dict con entity_type -> Set[str] de valores permitidos
        """
        enabled = self.config.get('enabled_entities', [])
        
        whitelists = {}
        for entity_type in enabled:
            getter_name = f"get_{entity_type}s"  # Pluralizar
            if hasattr(self, getter_name):
                whitelists[entity_type] = getattr(self, getter_name)()
        
        return whitelists
    
    def is_entity_enabled(self, entity_type: str) -> bool:
        """Verifica si un tipo de entidad está habilitado."""
        enabled = self.config.get('enabled_entities', [])
        disabled = self.config.get('disabled_entities', [])
        
        if entity_type in disabled:
            return False
        
        return entity_type in enabled
    
    def reload(self):
        """Recarga todas las whitelists desde disco."""
        self._cache.clear()
        self.config = self._load_config()
        print("✅ Whitelists recargadas desde archivos YAML")


# ============================================================================
# REGEX PATTERNS PARA EXTRACCIÓN AVANZADA
# ============================================================================

class EntityPatterns:
    """Patrones regex para capturar entidades complejas."""
    
    def __init__(self, patterns_file: str = "config/entity_patterns.yaml"):
        """Carga patrones desde YAML."""
        self.patterns_file = Path(patterns_file)
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """Carga patrones regex desde YAML."""
        if not self.patterns_file.exists():
            return self._default_patterns()
        
        with open(self.patterns_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _default_patterns(self) -> Dict:
        """Patrones por defecto si no existe archivo."""
        return {
            'variety': [
                r'arroz\s+(largo|redondo|bomba|basmati|integral|vaporizado)',
                r'(long|round|brown|parboiled)\s+grain\s+rice',
                r'rice\s+(variety|type):\s+(\w+)',
            ],
            'product': [
                r'harina\s+de\s+arroz\s+(\w+)',
                r'rice\s+(flour|starch|protein|semolina)',
                r'almidón\s+de\s+arroz\s+(nativo|modificado)',
            ],
            'metric': [
                r'(\d+[\d,\.]*)\s*(toneladas|tons|kg|mt)',
                r'(revenue|ingresos|ventas):\s*€?\$?\s*(\d+[\d,\.]*)',
                r'(\d+[\d,\.]*)\s*%',
            ]
        }
    
    def get_patterns(self, entity_type: str) -> List[str]:
        """Obtiene patrones regex para un tipo de entidad."""
        return self.patterns.get(entity_type, [])
    
    def compile_patterns(self, entity_type: str) -> List[re.Pattern]:
        """Compila patrones a objetos regex."""
        patterns = self.get_patterns(entity_type)
        return [re.compile(p, re.IGNORECASE) for p in patterns]


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Cargar whitelists
    loader = WhitelistLoader("whitelists")
    
    print("=== VARIEDADES CARGADAS ===")
    varieties = loader.get_varieties()
    print(f"Total: {len(varieties)}")
    print(f"Primeras 10: {list(varieties)[:10]}")
    
    print("\n=== PRODUCTOS CARGADOS ===")
    products = loader.get_products()
    print(f"Total: {len(products)}")
    
    print("\n=== EMPRESAS CARGADAS ===")
    companies = loader.get_companies()
    print(f"Total: {len(companies)}")
    
    print("\n=== ENTIDADES ACTIVAS ===")
    enabled = loader.config.get('enabled_entities', [])
    disabled = loader.config.get('disabled_entities', [])
    print(f"Activas: {', '.join(enabled)}")
    print(f"Desactivadas: {', '.join(disabled)}")
    
    print("\n=== VERIFICACIÓN ENTITY TYPES ===")
    print(f"¿PERSON habilitado? {loader.is_entity_enabled('person')}")
    print(f"¿VARIETY habilitado? {loader.is_entity_enabled('variety')}")
    
    # Cargar patrones regex
    patterns = EntityPatterns("config/entity_patterns.yaml")
    variety_patterns = patterns.compile_patterns('variety')
    print(f"\n=== PATRONES REGEX VARIETY ===")
    for p in variety_patterns:
        print(f"- {p.pattern}")
```

---

## 🔌 3. Integración con prompt.py

### Modificaciones necesarias en `prompt.py`

**ANTES** (hardcoded):
```python
# En tu prompt.py actual
VARIETY_WHITELIST = {
    "bomba", "basmati", "largo", "redondo", ...
}

PRODUCT_WHITELIST = {
    "arroz", "harina de arroz", ...
}
```

**DESPUÉS** (carga dinámica):
```python
# Al inicio de prompt.py
from whitelist_loader import WhitelistLoader, EntityPatterns

# Cargar whitelists
loader = WhitelistLoader("whitelists")

# Obtener whitelists por entidad
VARIETY_WHITELIST = loader.get_varieties()
PRODUCT_WHITELIST = loader.get_products()
BRAND_WHITELIST = loader.get_brands()
COMPANY_WHITELIST = loader.get_companies()
FACILITY_WHITELIST = loader.get_facilities()
COUNTRY_WHITELIST = loader.get_countries()
REGION_WHITELIST = loader.get_regions()
MARKET_WHITELIST = loader.get_markets()
METRIC_WHITELIST = loader.get_metrics()
STANDARD_WHITELIST = loader.get_standards()

# Cargar patrones regex
patterns = EntityPatterns("config/entity_patterns.yaml")

# PERSON ya NO está en enabled_entities (eliminado en config.yaml)
ENABLED_ENTITIES = loader.config.get('enabled_entities', [])
print(f"✅ Entidades activas: {', '.join(ENABLED_ENTITIES)}")
```

### Eliminación de PERSON en el prompt

En tu función de extracción de entidades, **eliminar completamente** las referencias a `person`:

**ANTES**:
```python
entity_types = [
    ("VARIETY", "rice variety"),
    ("PRODUCT", "rice product"),
    ("BRAND", "brand name"),
    ("COMPANY", "company name"),
    ("PERSON", "person name"),  # ❌ ELIMINAR ESTA LÍNEA
    ...
]
```

**DESPUÉS**:
```python
# Cargar dinámicamente desde config
entity_types = [
    (etype.upper(), f"{etype} name") 
    for etype in ENABLED_ENTITIES
]
# person no aparecerá porque está en disabled_entities
```

---

## 🧪 4. Script de validación

### `validate_whitelists.py`
```python
"""
Script de validación de whitelists YAML.
Verifica estructura, duplicados y carga correcta.
"""

from whitelist_loader import WhitelistLoader, EntityPatterns
from pathlib import Path


def validate_structure():
    """Valida que existan todos los archivos YAML necesarios."""
    print("=== VALIDACIÓN ESTRUCTURA ===")
    required_files = [
        "config.yaml",
        "varieties.yaml",
        "products.yaml",
        "brands.yaml",
        "companies.yaml",
        "facilities.yaml",
        "countries.yaml",
        "regions.yaml",
        "markets.yaml",
        "metrics.yaml",
        "standards.yaml"
    ]
    
    whitelists_dir = Path("whitelists")
    missing = []
    
    for filename in required_files:
        filepath = whitelists_dir / filename
        if filepath.exists():
            print(f"✅ {filename}")
        else:
            print(f"❌ {filename} NO ENCONTRADO")
            missing.append(filename)
    
    if missing:
        print(f"\n⚠️  Faltan {len(missing)} archivos")
        return False
    
    print("\n✅ Todos los archivos presentes")
    return True


def validate_loading():
    """Valida que las whitelists se carguen correctamente."""
    print("\n=== VALIDACIÓN CARGA ===")
    
    try:
        loader = WhitelistLoader("whitelists")
        
        checks = [
            ("varieties", loader.get_varieties),
            ("products", loader.get_products),
            ("brands", loader.get_brands),
            ("companies", loader.get_companies),
            ("facilities", loader.get_facilities),
            ("countries", loader.get_countries),
            ("regions", loader.get_regions),
            ("markets", loader.get_markets),
            ("metrics", loader.get_metrics),
            ("standards", loader.get_standards),
        ]
        
        for name, getter in checks:
            data = getter()
            print(f"✅ {name}: {len(data)} entradas")
        
        print("\n✅ Todas las whitelists se cargan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al cargar whitelists: {e}")
        return False


def validate_duplicates():
    """Detecta duplicados después de normalización."""
    print("\n=== VALIDACIÓN DUPLICADOS ===")
    
    loader = WhitelistLoader("whitelists")
    
    # Comprobar variedades (más propensas a duplicados)
    from collections import Counter
    
    varieties_raw = []
    data = loader._load_yaml('varieties.yaml')
    
    for variety_key, translations in data.get('varieties', {}).items():
        for lang_key in ['spanish', 'english']:
            if lang_key in translations:
                varieties_raw.extend(translations[lang_key])
    
    # Normalizar
    normalized = [loader._normalize(v) for v in varieties_raw]
    
    # Buscar duplicados
    counts = Counter(normalized)
    duplicates = {k: v for k, v in counts.items() if v > 1}
    
    if duplicates:
        print(f"⚠️  Encontrados {len(duplicates)} duplicados:")
        for dup, count in duplicates.items():
            print(f"  - '{dup}' aparece {count} veces")
        return False
    
    print("✅ No hay duplicados en varieties")
    return True


def validate_person_disabled():
    """Verifica que PERSON esté desactivado."""
    print("\n=== VALIDACIÓN PERSON DESACTIVADO ===")
    
    loader = WhitelistLoader("whitelists")
    
    enabled = loader.config.get('enabled_entities', [])
    disabled = loader.config.get('disabled_entities', [])
    
    if 'person' in disabled:
        print("✅ PERSON está en disabled_entities")
    else:
        print("⚠️  PERSON NO está en disabled_entities")
    
    if 'person' not in enabled:
        print("✅ PERSON NO está en enabled_entities")
    else:
        print("❌ PERSON está ACTIVO en enabled_entities")
        return False
    
    if not loader.is_entity_enabled('person'):
        print("✅ is_entity_enabled('person') = False")
        return True
    else:
        print("❌ is_entity_enabled('person') = True")
        return False


def validate_regex_patterns():
    """Valida que los patrones regex sean válidos."""
    print("\n=== VALIDACIÓN PATRONES REGEX ===")
    
    try:
        patterns = EntityPatterns("config/entity_patterns.yaml")
        
        for entity_type in ['variety', 'product', 'metric']:
            compiled = patterns.compile_patterns(entity_type)
            print(f"✅ {entity_type}: {len(compiled)} patrones")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al compilar patrones: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("VALIDACIÓN DE WHITELISTS EXTERNALIZADAS")
    print("=" * 60)
    
    results = [
        validate_structure(),
        validate_loading(),
        validate_duplicates(),
        validate_person_disabled(),
        validate_regex_patterns(),
    ]
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ TODAS LAS VALIDACIONES PASADAS")
    else:
        print(f"❌ {sum(not r for r in results)} VALIDACIONES FALLIDAS")
    print("=" * 60)
```

---

## 📝 5. Archivo de patrones regex

### `config/entity_patterns.yaml`
```yaml
# Patrones regex para extracción avanzada de entidades
# Estos patrones capturan variantes complejas no cubiertas por whitelists exactas

variety:
  # Patrón: ARROZ + VARIEDAD
  - 'arroz\s+(largo|redondo|bomba|basmati|integral|vaporizado|salvaje|thai|jasmin|sushi)'
  
  # Patrón: VARIEDAD + rice
  - '(long|round|brown|parboiled|bomba|basmati|wild|jasmine|sushi)\s+grain\s+rice'
  - '(bomba|basmati|jasmine|sushi)\s+rice'
  
  # Patrón: tipo de/variety of
  - '(tipo|variedad)\s+de\s+arroz:\s*(\w+)'
  - 'rice\s+(variety|type):\s*(\w+)'
  
  # Patrón: Exóticos + tipo
  - 'exóticos\s+(risotto|thai|jazmin|sushi|salvaje|origen)'

product:
  # Patrón: HARINA + especificación
  - 'harina\s+de\s+arroz\s+(fina|integral|precocida|gelatinizada)'
  - 'rice\s+flour\s+(fine|brown|precooked|gelatinized)'
  
  # Patrón: ALMIDÓN + tipo
  - 'almidón\s+de\s+arroz\s+(nativo|modificado)'
  - 'rice\s+starch\s+(native|modified)'
  
  # Patrón: productos derivados
  - 'rice\s+(flour|starch|protein|semolina|bran)'
  - '(concentrado|aislado)\s+de?\s+proteína\s+de\s+arroz'

metric:
  # Patrón: cantidades con unidades
  - '(\d+[\d,\.]*)\s*(toneladas|tons?|kg|mt|quintales)'
  
  # Patrón: valores monetarios
  - '(revenue|ingresos|ventas|facturación):\s*[€$]?\s*(\d+[\d,\.]*)\s*(millones?|M|K)?'
  
  # Patrón: porcentajes
  - '(\d+[\d,\.]*)\s*%\s*(crecimiento|aumento|reducción|margen)'
  
  # Patrón: capacidad de producción
  - 'capacidad\s+de\s+(\d+[\d,\.]*)\s*(t/año|toneladas/año)'

company:
  # Patrón: nombres con S.A., S.L., etc.
  - '(\w+(?:\s+\w+)*)\s*,?\s*(S\.A\.|S\.L\.|COOP\.|SL|SA)'
  
  # Patrón: Grupo + nombre
  - 'Grupo\s+(\w+(?:\s+\w+)*)'
  - '(\w+)\s+Group'

brand:
  # Marcas entre comillas
  - '"([^"]+)"\s+brand'
  - 'marca\s+"([^"]+)"'

facility:
  # Patrón: instalaciones con ubicación
  - '(planta|fábrica|factoría)\s+de\s+(\w+)'
  - '(plant|factory)\s+in\s+(\w+)'
  
  # Patrón: instalaciones con tipo
  - '(almacén|warehouse|silo)\s+de\s+(arroz|rice)'

# Patrones de exclusión (para filtrar falsos positivos)
exclude:
  # No capturar años como métricas
  - '(19|20)\d{2}'
  
  # No capturar porcentajes solos sin contexto
  - '^\d+%$'
  
  # No capturar fechas
  - '\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
```

---

## 🚀 Next Steps

### Paso 1: Crear estructura de directorios
```bash
cd /path/to/lightrag
mkdir -p whitelists config
```

### Paso 2: Crear archivos YAML
Copia los contenidos de arriba en:
- `whitelists/config.yaml`
- `whitelists/varieties.yaml`
- `whitelists/products.yaml`
- `whitelists/brands.yaml`
- `whitelists/companies.yaml`
- `whitelists/facilities.yaml`
- `whitelists/countries.yaml`
- `whitelists/regions.yaml`
- `whitelists/markets.yaml`
- `whitelists/metrics.yaml`
- `whitelists/standards.yaml`
- `config/entity_patterns.yaml`

### Paso 3: Crear `whitelist_loader.py`
Copia el código del gestor de whitelists

### Paso 4: Modificar tu `prompt.py`
**IMPORTANTE**: Súbeme tu `prompt.py` actual para integrarlo correctamente

### Paso 5: Validar
```bash
python validate_whitelists.py
```

### Paso 6: Completar whitelists faltantes
**CRÍTICO**: Necesito que me digas:
1. ¿Qué variedades faltan en tu graphml actual?
2. ¿Tu whitelist actual tiene más marcas/productos que no he incluido?

### Paso 7: Test de extracción
Probar con documento real y verificar:
- ✅ No aparecen PERSON
- ✅ LARGO/Largo se normalizan
- ✅ Regex captura "ARROZ LARGO"
- ✅ No hay duplicados

---

## 📊 Ventajas del nuevo sistema

| Aspecto | Antes | Después |
|---------|-------|---------|
| **Mantenimiento** | Editar código Python | Editar YAML sin tocar código |
| **Duplicados** | LARGO/Largo como nodos separados | Normalización automática |
| **Traducciones** | Hardcoded español/inglés mezclados | Fusión automática configurable |
| **Regex** | No disponibles | Patrones avanzados en YAML |
| **PERSON** | Activo (genera ruido) | Desactivado en config |
| **Escalabilidad** | Agregar variedad = modificar código | Agregar línea en YAML |
| **Versionado** | Git diff en código complejo | Git diff limpio en YAML |

---

## ⚠️ Advertencias

1. **Backup obligatorio**: Guarda tu `prompt.py` actual antes de modificar
2. **Testing exhaustivo**: Valida con documentos reales antes de producción
3. **Completar whitelists**: Los YAMLs de arriba son **base mínima**, necesitas completarlos con TU catálogo completo
4. **Dependencia PyYAML**: Asegúrate de tener `pip install pyyaml`

---

## 🎯 Qué necesito de ti ahora

1. ✅ **Tu `prompt.py` completo** (para integrarlo sin romper nada)
2. ✅ **Lista de variedades faltantes** (las que ves en el graphml pero no están)
3. ✅ **Confirmación de ruta** donde está tu LightRAG (para paths correctos)
4. ⚠️ **¿Hay más entidades UNKNOWN que quieras filtrar?** (vi 5 en el graphml)

**Súbeme el `prompt.py` y seguimos** 🚀
