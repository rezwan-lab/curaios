"""
Core normalization functions for various input types
such as organisms, diseases, and data types.

CurAIos - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union

from config.constants import InputType, SPECIAL_CASE_INPUTS, DATA_TYPE_VARIANTS
from config.mappings import ORGANISM_MAPPINGS, DISEASE_MAPPINGS, DATA_TYPE_MAPPINGS
from external.ncbi_taxonomy import query_ncbi_taxonomy
from external.ncbi_mesh import query_ncbi_mesh
from core.llm_service import get_llm_service
from utils.fuzzy_matching import fuzzy_match, find_best_match
from utils.error_handling import NormalizationError

logger = logging.getLogger(__name__)


def normalize_input(input_value: str, input_type: str) -> Dict[str, Any]:
    """
    Normalize user input to canonical forms.
    Args:
        input_value: The user input string to normalize
        input_type: The type of input ('organism', 'disease', 'data_type')
    Returns:Dictionary with normalized information
    Raises:NormalizationError: If normalization fails
    """
    logger.info(f"Normalizing {input_type}: {input_value}")
    
    if not input_value:
        raise NormalizationError(f"Empty input for {input_type}")
    
    cleaned_input = clean_input(input_value)
    
    if cleaned_input.lower() in SPECIAL_CASE_INPUTS:
        special_case = SPECIAL_CASE_INPUTS[cleaned_input.lower()]
        if special_case["type"] == input_type:
            logger.info(f"Detected special case input: {cleaned_input}")
            return handle_special_case(cleaned_input.lower(), input_type)
    
    try:
        if input_type == InputType.ORGANISM.value:
            return normalize_organism(cleaned_input)
        elif input_type == InputType.DISEASE.value:
            return normalize_disease(cleaned_input)
        elif input_type == InputType.DATA_TYPE.value:
            return normalize_data_type(cleaned_input)
        else:
            return normalize_generic(cleaned_input)
    except Exception as e:
        logger.error(f"Error normalizing {input_type} input: {e}", exc_info=True)
        return {
            "canonical_name": cleaned_input.capitalize(),
            "confidence": 0.5,
            "original_input": input_value,
            "source": "fallback"
        }


def normalize_organism(input_value: str) -> Dict[str, Any]:
    """
    Normalize organism name using NCBI Taxonomy database.
    Args:input_value: The organism name to normalize
    Returns:Dictionary with normalized organism information
    """
    # First, exact match in local mappings
    lowercase_input = input_value.lower()
    if lowercase_input in ORGANISM_MAPPINGS:
        result = ORGANISM_MAPPINGS[lowercase_input].copy()
        result["confidence"] = 1.0
        result["original_input"] = input_value
        result["source"] = "local_mapping"
        return result
        
    # Second, NCBI Taxonomy API
    try:
        ncbi_result = query_ncbi_taxonomy(input_value)
        if ncbi_result and ncbi_result.get("canonical_name"):
            ncbi_result["original_input"] = input_value
            ncbi_result["source"] = "ncbi_taxonomy"
            return ncbi_result
    except Exception as e:
        logger.warning(f"NCBI Taxonomy API lookup failed: {e}")
    
    # Third, fuzzy matching with local mappings
    best_match, score = find_best_match(
        input_value, 
        list(ORGANISM_MAPPINGS.keys()),
        threshold=0.85
    )
    
    if best_match:
        result = ORGANISM_MAPPINGS[best_match].copy()
        result["confidence"] = score
        result["original_input"] = input_value
        result["source"] = "fuzzy_mapping"
        return result
        
    # Finally, LLM for semantic matching
    llm_service = get_llm_service()
    llm_result = llm_service.validate_entity(input_value, "organism")
    
    llm_result["original_input"] = input_value
    llm_result["source"] = "llm"
    
    return llm_result


def normalize_disease(input_value: str) -> Dict[str, Any]:
    """
    Normalize disease name using NCBI MeSH database.
    Args:input_value: The disease name to normalize  
    Returns:Dictionary with normalized disease information
    """
    # First, exact match in local mappings
    lowercase_input = input_value.lower()
    if lowercase_input in DISEASE_MAPPINGS:
        result = DISEASE_MAPPINGS[lowercase_input].copy()
        result["confidence"] = 1.0
        result["original_input"] = input_value
        result["source"] = "local_mapping"
        return result
        
    # Second, NCBI MeSH API
    try:
        mesh_result = query_ncbi_mesh(input_value)
        if mesh_result and mesh_result.get("canonical_name"):
            mesh_result["original_input"] = input_value
            mesh_result["source"] = "ncbi_mesh"
            return mesh_result
    except Exception as e:
        logger.warning(f"NCBI MeSH API lookup failed: {e}")
    
    # Third, fuzzy matching with local mappings
    best_match, score = find_best_match(
        input_value, 
        list(DISEASE_MAPPINGS.keys()),
        threshold=0.85
    )
    
    if best_match:
        result = DISEASE_MAPPINGS[best_match].copy()
        result["confidence"] = score
        result["original_input"] = input_value
        result["source"] = "fuzzy_mapping"
        return result
        
    # Finally, LLM for semantic matching
    llm_service = get_llm_service()
    llm_result = llm_service.validate_entity(input_value, "disease")
    
    # Enrich result with additional information
    llm_result["original_input"] = input_value
    llm_result["source"] = "llm"
    
    return llm_result


def normalize_data_type(input_value: str) -> Dict[str, Any]:
    """
    Normalize experimental data type.
    Args:input_value: The data type to normalize
    Returns:Dictionary with normalized data type information
    """
    # First, exact match in local mappings
    lowercase_input = input_value.lower()
    if lowercase_input in DATA_TYPE_MAPPINGS:
        result = DATA_TYPE_MAPPINGS[lowercase_input].copy()
        result["confidence"] = 1.0
        result["original_input"] = input_value
        result["source"] = "local_mapping"
        return result
        
    # Second, fuzzy matching with local mappings
    best_match, score = find_best_match(
        input_value, 
        list(DATA_TYPE_MAPPINGS.keys()),
        threshold=0.85
    )
    
    if best_match:
        result = DATA_TYPE_MAPPINGS[best_match].copy()
        result["confidence"] = score
        result["original_input"] = input_value
        result["source"] = "fuzzy_mapping"
        return result
        
    # Third, check for keyword presence in variant mappings
    for canonical, variants in DATA_TYPE_VARIANTS.items():
        for variant in variants:
            if (variant.lower() in lowercase_input) or (lowercase_input in variant.lower()):
                return {
                    "canonical_name": canonical,
                    "confidence": 0.8,
                    "original_input": input_value,
                    "source": "keyword_match"
                }
                
    # Finally, LLM for semantic matching
    llm_service = get_llm_service()
    llm_result = llm_service.validate_entity(input_value, "data_type")
    
    # result with additional information
    llm_result["original_input"] = input_value
    llm_result["source"] = "llm"
    
    return llm_result


def normalize_generic(input_value: str) -> Dict[str, Any]:
    """
    Generic normalization for input types without specific handlers.
    Args:input_value: The input to normalize
    Returns:Dictionary with normalized information
    """
    cleaned = clean_input(input_value)
    
    return {
        "canonical_name": cleaned.capitalize(),
        "confidence": 0.7,
        "original_input": input_value,
        "source": "generic"
    }


def handle_special_case(input_value: str, input_type: str) -> Dict[str, Any]:
    """
    Handle special case inputs like 'virus' or 'cancer'.
    Args:
        input_value: The special case input
        input_type: The type of input 
    Returns:Dictionary with expanded information
    """
    special_case = SPECIAL_CASE_INPUTS[input_value]
    expansion = special_case.get("expansion", [])
    
    return {
        "canonical_name": input_value.capitalize(),
        "confidence": 0.9,
        "original_input": input_value,
        "source": "special_case",
        "is_special_case": True,
        "expanded_terms": expansion
    }


def clean_input(input_value: str) -> str:
    """
    Clean and standardize input text.
    Args:input_value: The input string to clean
    Returns:Cleaned string
    """

    cleaned = re.sub(r'\s+', ' ', input_value.strip())
    cleaned = re.sub(r'[^\w\s\-\.]', '', cleaned)
    
    return cleaned
