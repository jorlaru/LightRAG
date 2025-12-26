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
