"""
Input validation logic to ensure inputs meet requirements
before normalization and processing.
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

from config.constants import InputType, ERROR_MESSAGES
from utils.error_handling import ValidationError

logger = logging.getLogger(__name__)


def validate_input(input_value: str, input_type: str) -> str:
    logger.debug(f"Validating {input_type}: {input_value}")
    
    if input_value is None:
        raise ValidationError(f"Input for {input_type} cannot be None")

    input_str = str(input_value).strip()

    if not input_str:
        raise ValidationError(f"Input for {input_type} cannot be empty")

    if input_type == InputType.ORGANISM.value:
        return validate_organism(input_str)
    elif input_type == InputType.DISEASE.value:
        return validate_disease(input_str)
    elif input_type == InputType.DATA_TYPE.value:
        return validate_data_type(input_str)
    else:
        return validate_generic(input_str)


def validate_organism(input_value: str) -> str:

    cleaned = re.sub(r'[^\w\s\-\.]', '', input_value)
    
    if len(cleaned) < 2:
        raise ValidationError("Organism name is too short")
        
    lower_input = cleaned.lower()
    
    if lower_input in ["bacteria", "virus", "viruses", "fungi", "animal", "plant"]:
        logger.warning(f"Generic organism term detected: {lower_input}")
        
    disease_keywords = ["disease", "syndrome", "disorder", "infection", "cancer", "tumor"]
    if any(keyword in lower_input for keyword in disease_keywords):
        logger.warning(f"Input may be a disease rather than an organism: {input_value}")
        
    return cleaned


def validate_disease(input_value: str) -> str:
    cleaned = re.sub(r'[^\w\s\-\'\.]', '', input_value)

    if len(cleaned) < 2:
        raise ValidationError("Disease name is too short")
    lower_input = cleaned.lower()
    organism_keywords = ["bacteria", "virus", "human", "mouse", "animal", "homo sapiens", "mus musculus"]
    if any(keyword in lower_input for keyword in organism_keywords):
        logger.warning(f"Input may be an organism rather than a disease: {input_value}")
        
    return cleaned


def validate_data_type(input_value: str) -> str:
    cleaned = re.sub(r'[^\w\s\-\/\.]', '', input_value)

    if len(cleaned) < 2:
        raise ValidationError("Data type is too short")
    lower_input = cleaned.lower()
    
    if lower_input == "rna":
        logger.info("Converting standalone 'RNA' to 'RNAseq'")
        return "RNAseq"
        
    if lower_input == "scrna":
        logger.info("Converting standalone 'scRNA' to 'scRNAseq'")
        return "scRNAseq"
    generic_terms = ["sequencing", "analysis", "profiling", "data"]
    if lower_input in generic_terms:
        logger.warning(f"Input data type is too generic: {input_value}")
        
    return cleaned


def validate_generic(input_value: str) -> str:
    cleaned = re.sub(r'[^\w\s\-\/\.\,\'\"]', '', input_value)
    if len(cleaned) < 2:
        raise ValidationError("Input is too short")
    lower_input = cleaned.lower()
    dangerous_patterns = [
        r'\b(select|insert|update|delete|drop|create|alter)\b.*\b(from|table|database)\b',
        r'\b(union\s+all|union\s+select)\b',
        r'\-\-',
        r'\/\*.*\*\/',
        r'\bexec\b',
        r'\beval\b'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, lower_input):
            logger.warning(f"Potentially unsafe input detected: {input_value}")
            raise ValidationError("Input contains potentially unsafe patterns")
            
    return cleaned