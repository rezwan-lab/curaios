"""
Command-line interface for the Curaios.

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
from typing import Optional, List, Dict, Any

from config.constants import InputType, OutputFormat

logger = logging.getLogger(__name__)


def parse_arguments(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="BioData Curator: Dynamic Input Normalization and Semantic Validation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with organism and disease
  python main.py --organism "human" --disease "alzheimer's disease"
  
  # Specifying data type and minimum sample count
  python main.py --organism "mouse" --disease "diabetes" --data-type "RNAseq" --min-samples 10
  
  # Using date range and output format
  python main.py --organism "zebrafish" --disease "heart disease" --date-range "2018-2022" --format csv
  
  # Specifying repositories to search
  python main.py --organism "human" --disease "covid" --repositories "geo,zenodo,figshare"
  
  # Interactive mode
  python main.py --interactive
"""
    )
    
    input_group = parser.add_argument_group("Input Parameters")
    input_group.add_argument("--organism", type=str, help="Organism name (e.g., 'human', 'mouse')")
    input_group.add_argument("--disease", type=str, help="Disease name (e.g., 'alzheimer', 'diabetes')")
    input_group.add_argument("--data-type", type=str, help="Data type (e.g., 'RNAseq', 'microarray')")
    
    filter_group = parser.add_argument_group("Filter Parameters")
    filter_group.add_argument("--min-samples", type=int, help="Minimum number of samples")
    filter_group.add_argument("--date-range", type=str, 
                             help="Publication date range (e.g., '2020-2023' or '2020-01-01:2023-12-31')")
    filter_group.add_argument("--repositories", type=str,
                             help="Comma-separated list of repositories to search (e.g., 'geo,zenodo,figshare')")
    
    output_group = parser.add_argument_group("Output Parameters")
    output_group.add_argument("--output", "-o", type=str, help="Output file or directory path")
    output_group.add_argument("--format", "-f", type=str, choices=["json", "csv", "xlsx"],
                             default="json", help="Output format (default: json)")

    mode_group = parser.add_argument_group("Mode Parameters")
    mode_group.add_argument("--interactive", "-i", action="store_true",
                           help="Run in interactive mode with prompts")
    mode_group.add_argument("--quiet", "-q", action="store_true",
                           help="Suppress non-error output")
    mode_group.add_argument("--verbose", "-v", action="count", default=0,
                           help="Increase verbosity level (can be used multiple times)")

    config_group = parser.add_argument_group("Configuration Parameters")
    config_group.add_argument("--config", type=str, help="Path to configuration file")
    config_group.add_argument("--log-level", type=str, 
                             choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                             help="Logging level")
    config_group.add_argument("--log-file", type=str, help="Path to log file")

    parsed_args = parser.parse_args(args)

    if parsed_args.verbose > 0 and not parsed_args.log_level:
        if parsed_args.verbose == 1:
            parsed_args.log_level = "INFO"
        elif parsed_args.verbose == 2:
            parsed_args.log_level = "DEBUG"
        else:
            parsed_args.log_level = "DEBUG"
    if parsed_args.quiet and not parsed_args.log_level:
        parsed_args.log_level = "WARNING"
    
    return parsed_args


def print_results(results: Dict[str, Any], quiet: bool = False) -> None:

    if quiet:
        return
    
    print("\nResults:")
    
    if "query" in results:
        print(f"\nQuery: {results['query']}")

    result_count = results.get("results_count", 0)
    print(f"\nFound {result_count} results")

    if "sources" in results:
        print("\nResults by repository:")
        for repo, info in results["sources"].items():
            status = "✓" if info.get("success", False) else "✗"
            count = info.get("count", 0)
            print(f"  {status} {repo.upper()}: {count} results")
    
    if result_count > 0:
        print("\nSample results:")
        for i, result in enumerate(results.get("results", [])[:3]):
            print(f"\n[{i+1}] {result.get('title', 'No title')}")
            print(f"    Repository: {result.get('repository', 'Unknown')}")
            print(f"    URL: {result.get('url', 'N/A')}")
            
        if result_count > 3:
            print(f"\n... and {result_count - 3} more results")
    
    print("\nFull results have been saved to the output files (JSON and CSV).")


def format_input_summary(organism: Optional[Dict[str, Any]] = None,
                        disease: Optional[Dict[str, Any]] = None,
                        data_type: Optional[Dict[str, Any]] = None) -> str:
    summary_parts = []
    
    if organism:
        organism_str = f"Organism: {organism['canonical_name']}"
        if "ncbi_taxonomy_id" in organism:
            organism_str += f" (NCBI Taxonomy ID: {organism['ncbi_taxonomy_id']})"
        if "confidence" in organism and organism["confidence"] < 1.0:
            organism_str += f" (Confidence: {organism['confidence']:.2f})"
        summary_parts.append(organism_str)
    
    if disease:
        disease_str = f"Disease: {disease['canonical_name']}"
        if "mesh_id" in disease:
            disease_str += f" (MeSH ID: {disease['mesh_id']})"
        if "confidence" in disease and disease["confidence"] < 1.0:
            disease_str += f" (Confidence: {disease['confidence']:.2f})"
        summary_parts.append(disease_str)
    
    if data_type:
        data_type_str = f"Data Type: {data_type['canonical_name']}"
        if "confidence" in data_type and data_type["confidence"] < 1.0:
            data_type_str += f" (Confidence: {data_type['confidence']:.2f})"
        summary_parts.append(data_type_str)
    
    return "\n".join(summary_parts)