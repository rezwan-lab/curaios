"""
Query builder functions for constructing search queries
based on normalized inputs.

CurAIos - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab

"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import re

from core.llm_service import get_llm_service
from config.constants import SPECIAL_CASE_INPUTS

logger = logging.getLogger(__name__)


def build_search_query(organism: Optional[Dict[str, Any]] = None,
                      disease: Optional[Dict[str, Any]] = None,
                      data_type: Optional[Dict[str, Any]] = None,
                      min_samples: Optional[int] = None,
                      date_range: Optional[str] = None,
                      additional_filters: Optional[Dict[str, Any]] = None) -> str:
    """
    Build a comprehensive search query based on normalized inputs.
    Args:
        organism: Normalized organism information (optional)
        disease: Normalized disease information (optional)
        data_type: Normalized data type information (optional)
        min_samples: Minimum number of samples (optional)
        date_range: Publication date range (optional)
        additional_filters: Additional search filters (optional)
    Returns:Constructed search query string
    """
    logger.info("Building search query")
    
    organism_name = organism.get("canonical_name") if organism else None
    disease_name = disease.get("canonical_name") if disease else None
    data_type_name = data_type.get("canonical_name") if data_type else None
    
    expanded_terms = []
    
    if organism and organism.get("is_special_case"):
        expanded_terms.extend([f"({term})" for term in organism.get("expanded_terms", [])])
        organism_name = f"({' OR '.join(expanded_terms)})" if expanded_terms else organism_name
        
    if disease and disease.get("is_special_case"):
        expanded_terms = []
        expanded_terms.extend([f"({term})" for term in disease.get("expanded_terms", [])])
        disease_name = f"({' OR '.join(expanded_terms)})" if expanded_terms else disease_name
    
    base_query_parts = []
    
    if organism_name:
        base_query_parts.append(f"organism:({organism_name})")
        
    if disease_name:
        base_query_parts.append(f"disease:({disease_name})")
        
    if data_type_name:
        base_query_parts.append(f"data_type:({data_type_name})")
    
    filter_parts = []
    
    if min_samples:
        filter_parts.append(f"samples:>={min_samples}")
        
    if date_range:
        filter_parts.append(parse_date_range(date_range))

    if additional_filters:
        for key, value in additional_filters.items():
            filter_parts.append(f"{key}:{value}")

    query = " AND ".join(base_query_parts) if base_query_parts else ""
    filters = " AND ".join(filter_parts) if filter_parts else ""
    
    combined_query = f"{query} {filters}" if filters else query
    if organism_name or disease_name or data_type_name:
        try:
            llm_query = enhance_query_with_llm(organism_name, disease_name, data_type_name)
            if llm_query and len(llm_query) > len(combined_query):
                logger.info("Using LLM-enhanced query")
                return llm_query
        except Exception as e:
            logger.warning(f"Failed to enhance query with LLM: {e}")
    
    return combined_query


def enhance_query_with_llm(organism=None, disease=None, data_type=None):
    """
    Use LLM to enhance the search query with relevant synonyms and terms.
    Args:
        organism: Normalized organism name (optional)
        disease: Normalized disease name (optional)
        data_type: Normalized data type name (optional)
    Returns:Enhanced search query string
    """
    if not (organism or disease or data_type):
        return ""
        
    llm_service = get_llm_service()
    
    try:
        if hasattr(llm_service, 'expand_search_query'):
            return llm_service.expand_search_query(organism, disease, data_type)
        else:
            logger.warning("LLM service missing expand_search_query method, using local implementation")
            parts = []
            if organism:
                parts.append(organism)
            if disease:
                parts.append(disease)
            if data_type:
                parts.append(data_type)
                
            return " AND ".join(parts) if parts else ""
    except Exception as e:
        logger.warning(f"Failed to enhance query with LLM: {e}")
        return ""




def parse_date_range(date_range: str) -> str:
    """
    Parse and format a date range expression for search queries.
    Args:
        date_range: Date range string (e.g., "2020-2023" or "2020-01-01:2023-12-31")
    Returns:Formatted date range filter
    """
    year_pattern = r'^(\d{4})-(\d{4})$'
    year_match = re.match(year_pattern, date_range)
    
    if year_match:
        start_year = year_match.group(1)
        end_year = year_match.group(2)
        return f"publication_date:[{start_year}-01-01 TO {end_year}-12-31]"

    date_pattern = r'^(\d{4}-\d{2}-\d{2}):(\d{4}-\d{2}-\d{2})$'
    date_match = re.match(date_pattern, date_range)
    
    if date_match:
        start_date = date_match.group(1)
        end_date = date_match.group(2)
        return f"publication_date:[{start_date} TO {end_date}]"

    logger.warning(f"Unrecognized date range format: {date_range}")
    return f"publication_date:{date_range}"


def convert_to_api_parameters(query: str) -> Dict[str, Any]:
    """
    Convert a search query string to API-specific parameters.
    Args:
        query: The search query string
    Returns:
        Dictionary of API parameters
    """
    # This function would be customized based on the specific API being used
    # Here we provide a generic implementation
    
    # Parse the query to extract components
    params = {
        "query": query,
        "format": "json",
        "limit": 100,
        "sort": "relevance"
    }
    
    return params
