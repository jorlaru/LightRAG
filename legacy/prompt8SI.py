"""
LightRAG Prompts - Dacsa Group Edition
Versión: 1.5.0.3 FULL PRODUCTION (FIXED: entity_extraction_examples)
Fecha: 2024-12-26
"""

from __future__ import annotations
from typing import Any
import re

# ============================================================================
# 1. PRODUCT-VARIETY HIERARCHY (65 Industrial Specifications)
# ============================================================================

PRODUCT_WHITELIST = {'Rice', 'Maize', 'Wheat', 'Rye', 'Barley', 'Pulses'}

VARIETY_TO_PRODUCT_MAP = {
    # MAIZE (15)
    'Brewing Grits': 'Maize', 'Flaking Grits': 'Maize', 'Polenta Grits': 'Maize', 'Hominy Grits': 'Maize',
    'Maize Native Flour': 'Maize', 'Maize Precooked Flour': 'Maize', 'Maize Stabilized Flour': 'Maize',
    'Maize Heat-treated Flour': 'Maize', 'Maize Degerminated Flour': 'Maize', 'Masa Flour': 'Maize',
    'Maize Germ Raw': 'Maize', 'Maize Germ Toasted': 'Maize', 'Maize Bran': 'Maize', 'Maize Fiber': 'Maize', 'Maize Semolina': 'Maize',
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
    'Pea Protein Isolate': 'Pulses', 'Pulse Starch': 'Pulses', 'Pulse Fiber': 'Pulses', 'Toasted Pulse Flour': 'Pulses',
}

VARIETY_WHITELIST = set(VARIETY_TO_PRODUCT_MAP.keys())

# ============================================================================
# 2. SECTOR WHITELISTS (Anti-Noise)
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
# 3. ENTITY TYPES DEFINITION
# ============================================================================

DACSA_ENTITY_TYPES = """
## 1. COMPANY: Named business entities (e.g. Dacsa Group).
## 2. BRAND: Commercial brand names (e.g. La Fallera).
## 3. PRODUCT: Base commodities ONLY: Rice, Maize, Wheat, Rye, Barley, Pulses.
## 4. VARIETY: Specific industrial types (e.g. Japonica, Brewing Grits).
## 5. FACILITY: Physical plants (e.g. Sueca Plant).
## 6. PERSON: Name ONLY (no roles).
## 7. TECHNOLOGY: Keywords: {tech_list}
## 8. METRIC: Whitelist: {metric_list}
## 9. PROCESS: Whitelist: {process_list}
## 10. MARKET: Format: "ChannelName CountryName" (e.g. "HORECA Spain").
"""

# ============================================================================
# 4. PROMPTS (LightRAG System)
# ============================================================================

PROMPTS = {}
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##\n"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["entity_extraction_func"] = None 

# REGLA: LightRAG requiere obligatoriamente 'entity_extraction_examples' como una LISTA
PROMPTS['entity_extraction_examples'] = [
    """Example 1:
Input: "Dacsa processes Japonica rice at the Sueca Plant for the HORECA channel in Spain. EBITDA improved."
Output:
entity<|#|>Dacsa Group<|#|>Company<|#|>Leading European agribusiness company##
entity<|#|>Rice<|#|>Product<|#|>Base rice commodity##
entity<|#|>Japonica<|#|>Variety<|#|>Premium round grain rice variety##
entity<|#|>Sueca Plant<|#|>Facility<|#|>Rice processing facility located in Sueca##
entity<|#|>HORECA Spain<|#|>Market<|#|>Distribution channel for hotels and restaurants in Spain##
entity<|#|>EBITDA<|#|>Metric<|#|>Earnings before interest, taxes, depreciation and amortization##
relation<|#|>Dacsa Group<|#|>Sueca Plant<|#|>Operates processing facility<|#|>operations,facility<|#|>1.0##
relation<|#|>Japonica<|#|>Rice<|#|>Is a specific variety of<|#|>variety,product<|#|>1.0##
relation<|#|>Sueca Plant<|#|>Japonica<|#|>Processes variety<|#|>processing,variety<|#|>0.9##
<|COMPLETE|>"""
]

PROMPTS['entity_extraction_system_prompt'] = """
You are a specialized AI analyst for the agribusiness sector.
Extract entities and relationships in ENGLISH.

CRITICAL RULES:
1. NO generic terms (market, trend, growth).
2. NO numeric values, dates, or years as entities.
3. If a Variety is found, you MUST also extract its base Product and relate them.
4. Market Format: Always use "Channel Country" (no brackets).

ENTITY TYPES:
{entity_types}

OUTPUT FORMAT:
entity<|#|>entity_name<|#|>entity_type<|#|>entity_description##
relation<|#|>src_id<|#|>tgt_id<|#|>description<|#|>keywords<|#|>weight##
<|COMPLETE|>
"""

PROMPTS['entity_extraction_user_prompt'] = "### Context:\n{input_text}\n\n### Task:\nExtract entities. Output ends with <|COMPLETE|>"

PROMPTS['entity_continue_extraction_user_prompt'] = "Check for missing entities in: {input_text}\n<|COMPLETE|>"
PROMPTS['summarize_entity_descriptions'] = "Summarize: {description_list}"
PROMPTS['rag_response'] = "Context: {content_data}\nQuery: {user_prompt}\nAnswer in Spanish."
PROMPTS['keywords_extraction'] = "Keywords: {input_text}"
PROMPTS['naive_rag_response'] = "Context: {content_data}\nQuery: {user_prompt}"

# ============================================================================
# 5. INJECTION & VALIDATION
# ============================================================================

formatted_types = DACSA_ENTITY_TYPES.format(
    tech_list=', '.join(TECHNOLOGY_KEYWORDS),
    metric_list=', '.join(sorted(METRIC_WHITELIST)),
    process_list=', '.join(sorted(PROCESS_WHITELIST))
)

PROMPTS['entity_extraction_system_prompt'] = PROMPTS['entity_extraction_system_prompt'].format(
    entity_types=formatted_types
)

print("✅ prompt.py v1.5.0.3: Clave 'entity_extraction_examples' restaurada. Listo para procesar.")