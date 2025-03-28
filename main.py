#!/usr/bin/env python3
"""
Curaios - Main Entry Point
Curaios - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab
"""

import argparse
import logging
import sys
import os
import json
from pathlib import Path

# Set up base path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import init_settings, get_settings
from utils.logging_utils import setup_logging
from ui.cli import parse_arguments
from ui.interactive import interactive_mode
from core.normalization import normalize_input
from core.search_query import build_search_query
from core.validation import validate_input
from utils.file_operations import save_metadata
from external.data_retrieval import get_data_retriever


def main():
    """Main entry point for the BioData Curator application."""
    # Initialize settings
    init_settings()
    settings = get_settings()
    
    # Set up logging
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info("Starting CurAIos -  VERSION 0.0.1")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Use interactive mode if specified or if required inputs are missing
    if args.interactive or (not args.organism and not args.disease and not args.data_type):
        return interactive_mode()
    
    try:
        # Validate and normalize inputs
        logger.info("Validating and normalizing inputs")
        organism = validate_input(args.organism, 'organism') if args.organism else None
        disease = validate_input(args.disease, 'disease') if args.disease else None
        data_type = validate_input(args.data_type, 'data_type') if args.data_type else None
        
        normalized_organism = normalize_input(organism, 'organism') if organism else None
        normalized_disease = normalize_input(disease, 'disease') if disease else None
        normalized_data_type = normalize_input(data_type, 'data_type') if data_type else None
        
        # Build search query
        query = build_search_query(
            organism=normalized_organism,
            disease=normalized_disease,
            data_type=normalized_data_type,
            min_samples=args.min_samples,
            date_range=args.date_range
        )
        
        # Execute query and retrieve results from repositories
        logger.info(f"Executing search query: {query}")
        
        # Define which repositories to search
        repositories = []
        if args.repositories:
            repositories = args.repositories.split(',')
        
        # Get data retriever and fetch results
        data_retriever = get_data_retriever()
        
        # DEBUG: Print out data retriever information
        print("\n--- DEBUG: Data Retriever ---")
        print(f"Retriever type: {type(data_retriever)}")
        print(f"Retriever methods: {[m for m in dir(data_retriever) if not m.startswith('_') and callable(getattr(data_retriever, m))]}")
        
        # Fetch the results
        metadata = data_retriever.retrieve_all(
            query=query,
            output_dir=args.output or os.path.join("data", "output"),
            repositories=repositories
        )
        
        # DEBUG: Print the metadata structure
        print("\n--- DEBUG: Metadata Results ---")
        print(f"Type: {type(metadata)}")
        print(f"Keys: {metadata.keys() if isinstance(metadata, dict) else 'Not a dictionary'}")
        if isinstance(metadata, dict):
            print(f"Results count: {metadata.get('results_count', 'Missing')}")
            results = metadata.get('results', [])
            print(f"Results type: {type(results)}")
            print(f"Results length: {len(results)}")
            print(f"First result: {results[0] if results else 'No results'}")
        
        # Save results summary (data_retriever already saves detailed results)
        output_path = args.output or os.path.join("data", "output")
        save_metadata(metadata, output_path, args.format)
        
        # Final output
        logger.info(f"Results saved to {output_path}")
        print(f"\nMetadata retrieval complete. Found {metadata.get('results_count', 0)} results.")
        print(f"Results saved to {output_path}")
        
        # DEBUG: Show the first 2 results if they exist
        if isinstance(metadata, dict) and metadata.get('results'):
            results = metadata.get('results')
            print("\n--- First 2 Results: ---")
            for i, result in enumerate(results[:2]):
                print(f"Result {i+1}: {result.get('title', 'No title')} ({result.get('repository', 'Unknown')})")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
