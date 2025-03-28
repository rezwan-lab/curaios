#!/usr/bin/env python3
"""
BioData Curator - Integration Test Script

This script tests the integration between various components of the BioData Curator
to ensure they work together correctly.
"""

import os
import sys
import logging
import json
from typing import Dict, Any
from pathlib import Path

# Set up base path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import init_settings, get_settings
from utils.logging_utils import setup_logging
from core.normalization import normalize_input
from core.search_query import build_search_query
from core.validation import validate_input
from utils.file_operations import save_metadata
from external.data_retrieval import get_data_retriever


def test_complete_pipeline(organism: str = None, disease: str = None, data_type: str = None, 
                          output_dir: str = "data/output", repositories: str = None):
    """
    Test the complete pipeline from input to data retrieval.
    
    Args:
        organism: Organism name to search for
        disease: Disease name to search for
        data_type: Data type to search for
        output_dir: Directory to save results
        repositories: Comma-separated list of repositories to search
    """
    print("\n===== STARTING COMPLETE PIPELINE TEST =====")
    
    # Initialize settings
    init_settings()
    settings = get_settings()
    
    # Set up logging
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    
    # Create repositories list
    repo_list = repositories.split(',') if repositories else None
    
    try:
        print("\n--- Step 1: Validate Inputs ---")
        valid_organism = validate_input(organism, 'organism') if organism else None
        valid_disease = validate_input(disease, 'disease') if disease else None
        valid_data_type = validate_input(data_type, 'data_type') if data_type else None
        
        print(f"Organism validation: {valid_organism}")
        print(f"Disease validation: {valid_disease}")
        print(f"Data type validation: {valid_data_type}")
        
        print("\n--- Step 2: Normalize Inputs ---")
        norm_organism = normalize_input(valid_organism, 'organism') if valid_organism else None
        norm_disease = normalize_input(valid_disease, 'disease') if valid_disease else None
        norm_data_type = normalize_input(valid_data_type, 'data_type') if valid_data_type else None
        
        print(f"Normalized organism: {norm_organism}")
        print(f"Normalized disease: {norm_disease}")
        print(f"Normalized data type: {norm_data_type}")
        
        print("\n--- Step 3: Build Search Query ---")
        organism_name = norm_organism.get('canonical_name') if norm_organism else None
        disease_name = norm_disease.get('canonical_name') if norm_disease else None
        data_type_name = norm_data_type.get('canonical_name') if norm_data_type else None
        
        query = build_search_query(
            organism=norm_organism,
            disease=norm_disease,
            data_type=norm_data_type
        )
        
        print(f"Search query: {query}")
        
        print("\n--- Step 4: Retrieve Data ---")
        data_retriever = get_data_retriever()
        results = data_retriever.retrieve_all(
            query=query,
            output_dir=output_dir,
            repositories=repo_list
        )
        
        print(f"Total results: {results.get('results_count', 0)}")
        
        # Print results by repository
        for repo, info in results.get('sources', {}).items():
            print(f"  {repo.upper()}: {info.get('count', 0)} results")
        
        print("\n--- Step 5: First 3 Results Sample ---")
        for i, result in enumerate(results.get('results', [])[:3]):
            print(f"\nResult {i+1}:")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  Repository: {result.get('repository', 'N/A')}")
            print(f"  URL: {result.get('url', 'N/A')}")
        
        print("\n===== PIPELINE TEST COMPLETED SUCCESSFULLY =====")
        return results
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}", exc_info=True)
        print(f"\nERROR: Pipeline test failed: {e}")
        return None


def test_module_versions():
    """Test and print module versions for debugging."""
    print("\n===== MODULE VERSIONS =====")
    
    import requests
    import numpy
    
    print(f"Python: {sys.version}")
    print(f"Requests: {requests.__version__}")
    print(f"NumPy: {numpy.__version__}")
    
    print("===== END MODULE VERSIONS =====\n")


if __name__ == "__main__":
    # Print module versions for debugging
    test_module_versions()
    
    # Test parameters
    test_organism = "SARS-CoV-2"
    test_disease = "COVID-19"
    test_data_type = "RNAseq"
    test_repositories = "geo,figshare,zenodo"
    
    # Run the complete pipeline test
    results = test_complete_pipeline(
        organism=test_organism,
        disease=test_disease,
        data_type=test_data_type,
        repositories=test_repositories
    )
    
    # Print statistics
    if results:
        print(f"\nFound {results.get('results_count', 0)} total results for the query.")
        
        # Count by repository
        repo_counts = {}
        for result in results.get('results', []):
            repo = result.get('repository', 'unknown')
            repo_counts[repo] = repo_counts.get(repo, 0) + 1
        
        print("\nResults by repository:")
        for repo, count in repo_counts.items():
            print(f"  {repo}: {count} results")
