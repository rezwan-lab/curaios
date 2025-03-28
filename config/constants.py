"""
Constants, thresholds, and configuration values for the application.

CurAIos - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab
"""

from enum import Enum
from typing import Dict, List, Set


class InputType(Enum):
    ORGANISM = "organism"
    DISEASE = "disease"
    DATA_TYPE = "data_type"


class OutputFormat(Enum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "xlsx"

COMMON_VIRUSES = [
    "HIV",
    "SARS-CoV-2",
    "H1N1",
    "Ebola virus",
    "Zika virus",
    "Hepatitis C virus",
    "Human papillomavirus",
    "Influenza virus",
    "Herpes simplex virus",
    "Dengue virus"
]

DATA_TYPE_VARIANTS = {
    "RNAseq": ["rna-seq", "rna seq", "rnaseq", "rna sequencing", "transcriptomics"],
    "scRNAseq": ["single cell rna seq", "scrna-seq", "single-cell rna-seq", 
                 "single cell transcriptomics", "sc-rna-seq", "single cell sequencing"],
    "Microarray": ["array", "expression array", "gene expression array", "chip"],
    "WGS": ["whole genome sequencing", "genome sequencing", "complete genome"],
    "WES": ["whole exome sequencing", "exome sequencing", "exome"],
    "ATAC-seq": ["atac seq", "atacseq", "chromatin accessibility"],
    "ChIP-seq": ["chip seq", "chipseq", "chromatin immunoprecipitation"],
    "Proteomics": ["mass spectrometry", "ms/ms", "protein expression", "proteome"],
    "Metabolomics": ["metabolite profiling", "metabolite analysis", "metabolome"],
    "Metagenomics": ["metagenomic sequencing", "microbiome sequencing", "microbiome analysis"],
}

SPECIAL_CASE_INPUTS = {
    "virus": {"type": InputType.ORGANISM.value, "expansion": COMMON_VIRUSES},
    "viruses": {"type": InputType.ORGANISM.value, "expansion": COMMON_VIRUSES},
    "cancer": {"type": InputType.DISEASE.value, "expansion": ["neoplasm", "tumor", "carcinoma", "leukemia", "lymphoma"]},
    "infectious disease": {"type": InputType.DISEASE.value, "expansion": ["infection", "bacterial infection", "viral infection"]}
}

NCBI_TAXONOMY_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_TAXONOMY_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
NCBI_MESH_API = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_MESH_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

HTTP_MAX_RETRIES = 3
HTTP_RETRY_BACKOFF = 0.5  # seconds

LLM_PROMPTS = {
    "organism_validation": (
        "You are a biology expert tasked with identifying the correct organism name. "
        "Given the user input '{input}', identify the most likely organism name and "
        "respond in JSON format like this: {{\"canonical_name\": \"Homo sapiens\", "
        "\"ncbi_taxonomy_id\": 9606, \"confidence\": 0.95, \"alternatives\": [\"Human\"]}}. "
        "Use standard scientific nomenclature where applicable. "
        "If you are unsure, set a lower confidence score."
    ),
    "disease_validation": (
        "You are a medical expert tasked with identifying the correct disease name. "
        "Given the user input '{input}', identify the most likely disease name and "
        "respond in JSON format like this: {{\"canonical_name\": \"Alzheimer's Disease\", "
        "\"mesh_id\": \"D000544\", \"confidence\": 0.95, \"alternatives\": [\"Alzheimer Disease\", \"Dementia, Alzheimer Type\"]}}. "
        "Use standard medical terminology where applicable. "
        "If you are unsure, set a lower confidence score."
    ),
    "data_type_validation": (
        "You are a bioinformatics expert tasked with identifying the correct data type. "
        "Given the user input '{input}', identify the most likely experimental data type and "
        "respond in JSON format like this: {{\"canonical_name\": \"RNAseq\", "
        "\"confidence\": 0.95, \"alternatives\": [\"RNA sequencing\", \"Transcriptomics\"]}}. "
        "Use standard bioinformatics terminology where applicable. "
        "If you are unsure, set a lower confidence score."
    ),
    "query_expansion": (
        "You are a bioinformatics expert tasked with expanding a search query for biomedical datasets. "
        "Based on these normalized inputs: "
        "Organism: {organism}, Disease: {disease}, Data Type: {data_type}, "
        "generate a comprehensive search query that would find relevant datasets. "
        "Include relevant synonyms, abbreviations, and related terms. "
        "Format your response as a JSON object with a single 'query' field containing the expanded query string."
    )
}

ERROR_MESSAGES = {
    "api_timeout": "Connection to external API timed out. Please try again later.",
    "api_error": "Error communicating with external API: {error}",
    "validation_failed": "Failed to validate {input_type}: {input}",
    "normalization_failed": "Failed to normalize {input_type}: {input}",
    "no_results": "No results found for the given query parameters.",
    "plugin_error": "Error in plugin {plugin_name}: {error}"
}
