"""
Interactive prompt interface for the CurAIos.

Curaios - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab
"""

import logging
import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Union

from config.constants import InputType, OutputFormat
from config.settings import get_settings
from core.normalization import normalize_input
from core.search_query import build_search_query
from core.validation import validate_input
from utils.error_handling import ValidationError, NormalizationError, get_error_message
from utils.file_operations import save_metadata
from utils.logging_utils import get_audit_logger
from external.data_retrieval import get_data_retriever
from ui.cli import print_results

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()


def interactive_mode() -> int:
    """
    Run the application in interactive mode with prompts.
    Returns:Exit code (0 for success, non-zero for errors)
    """
    print("\n=== CurAIos - Interactive Mode ===\n")
    print("Please answer the following questions to normalize your inputs and search for metadata.")
    print("Press Enter without typing to skip optional questions.\n")
    
    # Collect inputs from user
    try:
        organism, disease, data_type = collect_primary_inputs()
        filters = collect_filters()
        repositories = collect_repositories()
        output_path, output_format = collect_output_preferences()

        display_normalization_summary(organism, disease, data_type)
        
        if not confirm_inputs():
            print("\nOperation cancelled by user.")
            return 0

        query = build_search_query(
            organism=organism,
            disease=disease,
            data_type=data_type,
            min_samples=filters.get("min_samples"),
            date_range=filters.get("date_range"),
            additional_filters=filters.get("additional")
        )
        
        print(f"\nGenerated search query: {query}")

        data_retriever = get_data_retriever()
        metadata = data_retriever.retrieve_all(
            query=query,
            output_dir=output_path,
            repositories=repositories
        )

        print_results(metadata)

        audit_logger.log_activity(
            action="interactive_search",
            details={
                "organism": organism["canonical_name"] if organism else None,
                "disease": disease["canonical_name"] if disease else None,
                "data_type": data_type["canonical_name"] if data_type else None,
                "query": query,
                "repositories": repositories,
                "results_count": metadata.get("results_count", 0)
            }
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        logger.error(f"Error in interactive mode: {e}", exc_info=True)
        print(f"\nError: {str(e)}")
        return 1


def collect_primary_inputs() -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Collect and normalize primary inputs from the user.
    Returns:Tuple containing normalized organism, disease, and data type information
    """
    organism = None
    organism_input = input("Organism (e.g., human, mouse, e. coli): ").strip()
    if organism_input:
        try:
            validated_organism = validate_input(organism_input, InputType.ORGANISM.value)
            organism = normalize_input(validated_organism, InputType.ORGANISM.value)
            logger.info(f"Normalized organism: {organism['canonical_name']}")
        except (ValidationError, NormalizationError) as e:
            logger.warning(f"Failed to normalize organism: {e}")
            print(f"Warning: {str(e)}")
            if confirm_with_user("Would you like to use the input as-is?"):
                organism = {
                    "canonical_name": organism_input.capitalize(),
                    "confidence": 0.5,
                    "original_input": organism_input,
                    "source": "user_override"
                }
    
    disease = None
    disease_input = input("Disease (e.g., alzheimer's, diabetes, cancer): ").strip()
    if disease_input:
        try:
            validated_disease = validate_input(disease_input, InputType.DISEASE.value)
            disease = normalize_input(validated_disease, InputType.DISEASE.value)
            logger.info(f"Normalized disease: {disease['canonical_name']}")
        except (ValidationError, NormalizationError) as e:
            logger.warning(f"Failed to normalize disease: {e}")
            print(f"Warning: {str(e)}")
            if confirm_with_user("Would you like to use the input as-is?"):
                disease = {
                    "canonical_name": disease_input.capitalize(),
                    "confidence": 0.5,
                    "original_input": disease_input,
                    "source": "user_override"
                }

    data_type = None
    data_type_input = input("Data type (e.g., RNAseq, microarray, proteomics): ").strip()
    if data_type_input:
        try:
            validated_data_type = validate_input(data_type_input, InputType.DATA_TYPE.value)
            data_type = normalize_input(validated_data_type, InputType.DATA_TYPE.value)
            logger.info(f"Normalized data type: {data_type['canonical_name']}")
        except (ValidationError, NormalizationError) as e:
            logger.warning(f"Failed to normalize data type: {e}")
            print(f"Warning: {str(e)}")
            if confirm_with_user("Would you like to use the input as-is?"):
                data_type = {
                    "canonical_name": data_type_input.capitalize(),
                    "confidence": 0.5,
                    "original_input": data_type_input,
                    "source": "user_override"
                }
    
    return organism, disease, data_type


def collect_filters() -> Dict[str, Any]:

    filters = {}

    min_samples_input = input("\nMinimum number of samples (optional): ").strip()
    if min_samples_input:
        try:
            min_samples = int(min_samples_input)
            filters["min_samples"] = min_samples
        except ValueError:
            print("Warning: Invalid number. Minimum samples filter will be ignored.")
    
    date_range_input = input("Publication date range (e.g., 2020-2023, optional): ").strip()
    if date_range_input:
        filters["date_range"] = date_range_input

    print("\nAdditional filters (optional)")
    print("Enter each filter in the format 'key:value', or press Enter to continue.")
    additional_filters = {}
    
    while True:
        filter_input = input("Additional filter (or Enter to continue): ").strip()
        if not filter_input:
            break

        if ":" in filter_input:
            key, value = filter_input.split(":", 1)
            additional_filters[key.strip()] = value.strip()
        else:
            print("Warning: Invalid filter format. Use 'key:value' format.")
    
    if additional_filters:
        filters["additional"] = additional_filters
    
    return filters


def collect_repositories() -> List[str]:

    available_repos = ["geo", "figshare", "zenodo", "osf", "sciencedb"]
    selected_repos = []
    
    print("\nSelect repositories to search:")
    print("Available repositories: " + ", ".join(available_repos))
    print("Enter 'all' to search all repositories, or list specific ones (comma-separated).")
    
    repo_input = input("Repositories (default: all): ").strip().lower()
    
    if not repo_input or repo_input == "all":
        selected_repos = available_repos
    else:
        input_repos = [r.strip() for r in repo_input.split(",")]

        for repo in input_repos:
            if repo in available_repos:
                selected_repos.append(repo)
            else:
                print(f"Warning: Unknown repository '{repo}'. It will be ignored.")
    
    print(f"Selected repositories: {', '.join(selected_repos)}")
    return selected_repos


def collect_output_preferences() -> Tuple[str, str]:

    settings = get_settings()

    default_output_dir = settings.output_dir

    output_path_input = input(f"\nOutput path (default: {default_output_dir}): ").strip()
    output_path = output_path_input if output_path_input else default_output_dir

    default_format = settings.default_output_format
    format_input = input(f"Output format [json, csv, xlsx] (default: {default_format}): ").strip().lower()
    
    output_format = None
    if format_input:
        if format_input in [f.value for f in OutputFormat]:
            output_format = format_input
        else:
            print(f"Warning: Invalid format '{format_input}'. Using default format.")
            output_format = default_format
    else:
        output_format = default_format
    
    return output_path, output_format


def display_normalization_summary(organism: Optional[Dict[str, Any]] = None,
                                 disease: Optional[Dict[str, Any]] = None,
                                 data_type: Optional[Dict[str, Any]] = None) -> None:
    print("\n=== Normalization Summary ===")
    
    if organism:
        print(f"\nOrganism:")
        print(f"  Original input: {organism.get('original_input', 'N/A')}")
        print(f"  Normalized to: {organism.get('canonical_name', 'N/A')}")
        if "ncbi_taxonomy_id" in organism:
            print(f"  NCBI Taxonomy ID: {organism['ncbi_taxonomy_id']}")
        if "confidence" in organism:
            print(f"  Confidence: {organism['confidence']:.2f}")
    
    if disease:
        print(f"\nDisease:")
        print(f"  Original input: {disease.get('original_input', 'N/A')}")
        print(f"  Normalized to: {disease.get('canonical_name', 'N/A')}")
        if "mesh_id" in disease:
            print(f"  MeSH ID: {disease['mesh_id']}")
        if "confidence" in disease:
            print(f"  Confidence: {disease['confidence']:.2f}")
    
    if data_type:
        print(f"\nData Type:")
        print(f"  Original input: {data_type.get('original_input', 'N/A')}")
        print(f"  Normalized to: {data_type.get('canonical_name', 'N/A')}")
        if "confidence" in data_type:
            print(f"  Confidence: {data_type['confidence']:.2f}")
    
    if not (organism or disease or data_type):
        print("No inputs provided for normalization.")


def confirm_inputs() -> bool:
    return confirm_with_user("\nProceed with these normalized inputs?")


def confirm_with_user(prompt: str) -> bool:
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no"]:
            return False
        else:
            print("Please enter 'y' or 'n'.")