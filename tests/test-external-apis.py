"""
Unit tests for external API client functionality.
Curaios - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from external.ncbi_taxonomy import query_ncbi_taxonomy, _extract_organism_info, _calculate_match_confidence
from external.ncbi_mesh import query_ncbi_mesh, _extract_disease_info
from utils.error_handling import APIError


class TestNCBITaxonomyClient(unittest.TestCase):

    @patch('external.ncbi_taxonomy.requests.get')
    def test_query_ncbi_taxonomy_success(self, mock_get):

        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "esearchresult": {
                "count": "1",
                "idlist": ["9606"]
            }
        }
        
        summary_response = MagicMock()
        summary_response.status_code = 200
        summary_response.json.return_value = {
            "result": {
                "uids": ["9606"],
                "9606": {
                    "scientificname": "Homo sapiens",
                    "commonname": "human",
                    "rank": "species",
                    "lineage": "Eukaryota; Metazoa; Chordata; Vertebrata; Mammalia; Primates; Hominidae",
                    "othernames": {
                        "synonym": ["H. sapiens"],
                        "genbank": ["man"]
                    }
                }
            }
        }

        mock_get.side_effect = [search_response, summary_response]

        result = query_ncbi_taxonomy("human")

        self.assertEqual(result["canonical_name"], "Homo sapiens")
        self.assertEqual(result["ncbi_taxonomy_id"], 9606)
        self.assertIn("human", result["alternatives"])
        self.assertGreaterEqual(result["confidence"], 0.8)

        self.assertEqual(mock_get.call_count, 2)
    
    @patch('external.ncbi_taxonomy.requests.get')
    def test_query_ncbi_taxonomy_no_results(self, mock_get):
        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "esearchresult": {
                "count": "0",
                "idlist": []
            }
        }
        
        mock_get.return_value = search_response

        result = query_ncbi_taxonomy("nonexistent organism")
        
        self.assertEqual(result, {})
        
        self.assertEqual(mock_get.call_count, 1)
    
    @patch('external.ncbi_taxonomy.requests.get')
    def test_query_ncbi_taxonomy_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("API Error")
        
        mock_get.return_value = mock_response
        
        with self.assertRaises(APIError):
            query_ncbi_taxonomy("human")
    
    def test_extract_organism_info(self):
        summary_data = {
            "result": {
                "uids": ["9606"],
                "9606": {
                    "scientificname": "Homo sapiens",
                    "commonname": "human",
                    "rank": "species",
                    "lineage": "Eukaryota; Metazoa; Chordata; Vertebrata; Mammalia; Primates; Hominidae",
                    "othernames": {
                        "synonym": ["H. sapiens"],
                        "genbank": ["man"]
                    }
                }
            }
        }

        result = _extract_organism_info(summary_data, "9606")

        self.assertEqual(result["canonical_name"], "Homo sapiens")
        self.assertEqual(result["ncbi_taxonomy_id"], 9606)
        self.assertEqual(result["rank"], "species")
        self.assertIn("human", result["alternatives"])
        self.assertIn("H. sapiens", result["alternatives"])
        self.assertIn("man", result["alternatives"])
    
    def test_calculate_match_confidence(self):
        self.assertEqual(_calculate_match_confidence("Homo sapiens", "Homo sapiens", []), 1.0)
        self.assertEqual(_calculate_match_confidence("human", "Homo sapiens", ["human", "man"]), 0.95)
        self.assertEqual(_calculate_match_confidence("homo", "Homo sapiens", []), 0.9)
        self.assertEqual(_calculate_match_confidence("sapien", "Homo sapiens", ["H. sapiens"]), 0.85)
        self.assertEqual(_calculate_match_confidence("hominid", "Homo sapiens", ["human"]), 0.8)


class TestNCBIMeshClient(unittest.TestCase):

    @patch('external.ncbi_mesh.requests.get')
    def test_query_ncbi_mesh_success(self, mock_get):
        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "esearchresult": {
                "count": "1",
                "idlist": ["D000544"]
            }
        }
        
        summary_response = MagicMock()
        summary_response.status_code = 200
        summary_response.json.return_value = {
            "result": {
                "uids": ["D000544"],
                "D000544": {
                    "descriptorname": "Alzheimer's Disease",
                    "ui": "D000544",
                    "scopenote": "A degenerative disease of the brain...",
                    "treenumberlist": ["C10.228.140.380"],
                    "conceptlist": [
                        {
                            "conceptname": "Alzheimer Disease",
                            "preferredconceptyn": "Y",
                            "termlist": [
                                {"termname": "Alzheimer's Disease", "termui": "T000001"},
                                {"termname": "Alzheimer Disease", "termui": "T000002"},
                                {"termname": "Alzheimer Dementia", "termui": "T000003"}
                            ]
                        },
                        {
                            "conceptname": "Presenile Dementia",
                            "preferredconceptyn": "N",
                            "termlist": [
                                {"termname": "Presenile Dementia", "termui": "T000004"}
                            ]
                        }
                    ]
                }
            }
        }
        
        mock_get.side_effect = [search_response, summary_response]
        result = query_ncbi_mesh("alzheimer")
        self.assertEqual(result["canonical_name"], "Alzheimer's Disease")
        self.assertEqual(result["mesh_id"], "D000544")
        self.assertIn("Alzheimer Disease", result["alternatives"])
        self.assertIn("Alzheimer Dementia", result["alternatives"])
        self.assertIn("Presenile Dementia", result["alternatives"])
        self.assertGreaterEqual(result["confidence"], 0.8)
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('external.ncbi_mesh.requests.get')
    def test_query_ncbi_mesh_no_results(self, mock_get):
        search_response = MagicMock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "esearchresult": {
                "count": "0",
                "idlist": []
            }
        }

        retry_response = MagicMock()
        retry_response.status_code = 200
        retry_response.json.return_value = {
            "esearchresult": {
                "count": "0",
                "idlist": []
            }
        }
        
        mock_get.side_effect = [search_response, retry_response]

        result = query_ncbi_mesh("nonexistent disease")
        self.assertEqual(result, {})
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('external.ncbi_mesh.requests.get')
    def test_query_ncbi_mesh_api_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response

        with self.assertRaises(APIError):
            query_ncbi_mesh("alzheimer")
    
    def test_extract_disease_info(self):
        summary_data = {
            "result": {
                "uids": ["D000544"],
                "D000544": {
                    "descriptorname": "Alzheimer's Disease",
                    "ui": "D000544",
                    "scopenote": "A degenerative disease of the brain...",
                    "treenumberlist": ["C10.228.140.380"],
                    "conceptlist": [
                        {
                            "conceptname": "Alzheimer Disease",
                            "preferredconceptyn": "Y",
                            "termlist": [
                                {"termname": "Alzheimer's Disease", "termui": "T000001"},
                                {"termname": "Alzheimer Disease", "termui": "T000002"},
                                {"termname": "Alzheimer Dementia", "termui": "T000003"}
                            ]
                        },
                        {
                            "conceptname": "Presenile Dementia",
                            "preferredconceptyn": "N",
                            "termlist": [
                                {"termname": "Presenile Dementia", "termui": "T000004"}
                            ]
                        }
                    ]
                }
            }
        }

        result = _extract_disease_info(summary_data, "D000544")

        self.assertEqual(result["canonical_name"], "Alzheimer's Disease")
        self.assertEqual(result["mesh_id"], "D000544")
        self.assertIn("Alzheimer Disease", result["alternatives"])
        self.assertIn("Alzheimer Dementia", result["alternatives"])
        self.assertIn("Presenile Dementia", result["alternatives"])


if __name__ == "__main__":
    unittest.main()
