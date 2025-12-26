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
