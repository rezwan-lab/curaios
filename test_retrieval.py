#!/usr/bin/env python3
"""
Test script for data retrieval with mock data.

Curaios - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Directory to save results
OUTPUT_DIR = "data/output"

def retrieve_mock_data(query: str):
    """Get mock data for testing."""
    logger.info(f"Retrieving mock data for query: {query}")
    
    # Create mock data for different repositories
    geo_data = [
        {
            "id": "200012345",
            "accession": "GSE156544",
            "title": "SARS-CoV-2 infection of human lung epithelium",
            "summary": "RNA-sequencing of lung epithelial cells infected with SARS-CoV-2",
            "organism": "Homo sapiens, SARS-CoV-2",
            "type": "dataset",
            "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE156544",
            "platform": "Illumina NovaSeq 6000",
            "samples": 24,
            "repository": "GEO"
        },
        {
            "id": "200012346",
            "accession": "GSE154998",
            "title": "COVID-19 patient bronchoalveolar immune cells",
            "summary": "Single-cell RNA-seq of immune cells from COVID-19 patients",
            "organism": "Homo sapiens",
            "type": "dataset",
            "url": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE154998",
            "platform": "10x Genomics",
            "samples": 18,
            "repository": "GEO"
        }
    ]
    
    figshare_data = [
        {
            "id": "12345678",
            "title": "SARS-CoV-2 genomic sequences from early pandemic",
            "url": "https://figshare.com/articles/dataset/12345678",
            "doi": "10.1234/figshare.12345678",
            "type": "dataset",
            "created_date": "2020-04-15",
            "authors": ["Zhang, L.", "Wang, J.", "Smith, A."],
            "description": "Genomic sequences of SARS-CoV-2 isolates collected in early 2020.",
            "repository": "Figshare"
        },
        {
            "id": "87654321",
            "title": "COVID-19 patient clinical data from hospital admissions",
            "url": "https://figshare.com/articles/dataset/87654321",
            "doi": "10.1234/figshare.87654321",
            "type": "dataset",
            "created_date": "2020-07-22",
            "authors": ["Johnson, M.", "Lee, K.", "Garcia, R."],
            "description": "Anonymized clinical data from COVID-19 patients admitted to hospitals.",
            "repository": "Figshare"
        }
    ]
    
    # Combine all data
    all_results = []
    all_results.extend(geo_data)
    all_results.extend(figshare_data)
    
    # Create result structure
    results = {
        "query": query,
        "results_count": len(all_results),
        "results": all_results,
        "sources": {
            "geo": {"count": len(geo_data), "success": True},
            "figshare": {"count": len(figshare_data), "success": True},
            "zenodo": {"count": 0, "success": False, "error": "Not implemented for this test"},
            "osf": {"count": 0, "success": False, "error": "Not implemented for this test"},
            "sciencedb": {"count": 0, "success": False, "error": "Not implemented for this test"}
        }
    }
    
    # Save results
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save as JSON
    json_path = os.path.join(OUTPUT_DIR, "test_results.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save as CSV
    csv_path = os.path.join(OUTPUT_DIR, "test_results.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        # Write header
        headers = set()
        for result in all_results:
            headers.update(result.keys())
        f.write(",".join(sorted(headers)) + "\n")
        
        # Write data
        for result in all_results:
            row = []
            for header in sorted(headers):
                value = result.get(header, "")
                if isinstance(value, list):
                    value = "|".join(value)
                # Escape commas in values
                if isinstance(value, str) and "," in value:
                    value = f'"{value}"'
                row.append(str(value))
            f.write(",".join(row) + "\n")
    
    logger.info(f"Mock results saved to {json_path} and {csv_path}")
    logger.info(f"Found {len(all_results)} mock results")
    
    return results

if __name__ == "__main__":
    query = "organism:(Severe acute respiratory syndrome coronavirus 2) AND disease:(COVID-19)"
    results = retrieve_mock_data(query)
    
    # Print summary
    print(f"Query: {results['query']}")
    print(f"Found {results['results_count']} results")
    print("\nResults by repository:")
    for repo, info in results["sources"].items():
        status = "✓" if info.get("success", False) else "✗"
        count = info.get("count", 0)
        print(f"  {status} {repo.upper()}: {count} results")
    
    # Print sample results
    if results["results_count"] > 0:
        print("\nSample results:")
        for i, result in enumerate(results["results"][:3]):
            print(f"\n[{i+1}] {result.get('title', 'No title')}")
            print(f"    Repository: {result.get('repository', 'Unknown')}")
            print(f"    URL: {result.get('url', 'N/A')}")
