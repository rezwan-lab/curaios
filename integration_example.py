#!/usr/bin/env python3
"""
Example of integrating Curaios as a library in another application.

Curaios - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab
"""

import os
import sys
import json
from pprint import pprint

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import BioData Curator components
from config.settings import init_settings, get_settings
from core.validation import validate_input
from core.normalization import normalize_input
from core.search_query import build_search_query
from utils.file_operations import save_metadata
from utils.logging_utils import setup_logging
from config.constants import InputType


def main():
    """Demonstrate BioData Curator integration."""
    # Initialize settings
    init_settings()
    settings = get_settings()
    
    # Set up logging
    setup_logging(log_level="INFO")
    
    print("BioData Curator Integration Example")
    print("===================================\n")
    
    # Example inputs
    example_inputs = [
        {"organism": "human", "disease": "alzheimer", "data_type": "rnaseq"},
        {"organism": "mouse", "disease": "diabetes type 2", "data_type": "single cell"},
        {"organism": "zebrafish", "disease": "heart development", "data_type": "atac-seq"},
        {"organism": "e. coli", "disease": None, "data_type": "rna-seq"},
        {"organism": "virus", "disease": "covid", "data_type": "sequencing"}
    ]
    
    for i, inputs in enumerate(example_inputs):
        print(f"\nExample {i+1}:")
        print(f"Inputs: {inputs}")
        
        # Validate and normalize inputs
        results = {}
        
        for input_type, input_value in inputs.items():
            if input_value is None:
                continue
                
            try:
                # Validate the input
                validated = validate_input(input_value, getattr(InputType, input_type.upper()).value)
                
                # Normalize the input
                normalized = normalize_input(validated, getattr(InputType, input_type.upper()).value)
                
                results[input_type] = normalized
                
                print(f"\n{input_type.capitalize()}:")
                print(f"  Original: {input_value}")
                print(f"  Normalized: {normalized['canonical_name']}")
                if "confidence" in normalized:
                    print(f"  Confidence: {normalized['confidence']:.2f}")
                if "alternatives" in normalized:
                    print(f"  Alternatives: {', '.join(normalized['alternatives'][:3])}")
                    
            except Exception as e:
                print(f"Error processing {input_type}: {str(e)}")
        
        # Build search query
        try:
            query = build_search_query(
                organism=results.get("organism"),
                disease=results.get("disease"),
                data_type=results.get("data_type")
            )
            
            print(f"\nGenerated query:")
            print(f"  {query}")
            
            # In a real application, you would use this query to retrieve metadata
            # For example:
            # metadata = retrieve_metadata(query)
            # save_metadata(metadata, f"example_{i+1}_results.json", "json")
            
        except Exception as e:
            print(f"Error building query: {str(e)}")
        
        print("\n" + "-" * 60)
    
    print("\nIntegration example complete!")


if __name__ == "__main__":
    main()
