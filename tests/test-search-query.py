"""
Unit tests for search query building functionality.
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
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.search_query import build_search_query, parse_date_range, enhance_query_with_llm


class TestSearchQuery(unittest.TestCase):
    
    def setUp(self):
        self.llm_patcher = patch('core.llm_service.get_llm_service')
        self.mock_llm = self.llm_patcher.start()
        self.mock_llm_instance = MagicMock()
        self.mock_llm.return_value = self.mock_llm_instance
        self.mock_llm_instance.expand_search_query.return_value = (
            '(human OR "Homo sapiens") AND (cancer OR neoplasm OR tumor OR carcinoma) AND (RNAseq OR "RNA sequencing" OR transcriptomics)'
        )
    
    def tearDown(self):
        self.llm_patcher.stop()
    
    def test_build_search_query_basic(self):
        organism = {"canonical_name": "Homo sapiens", "ncbi_taxonomy_id": 9606}
        disease = {"canonical_name": "Alzheimer's Disease", "mesh_id": "D000544"}
        data_type = {"canonical_name": "RNAseq"}
        query = build_search_query(
            organism=organism,
            disease=disease,
            data_type=data_type,
            min_samples=10,
            date_range="2020-2023"
        )
        self.assertIn("organism:(Homo sapiens)", query)
        self.assertIn("disease:(Alzheimer's Disease)", query)
        self.assertIn("data_type:(RNAseq)", query)
        self.assertIn("samples:>=10", query)
        self.assertIn("publication_date:[2020-01-01 TO 2023-12-31]", query)
    
    def test_build_search_query_partial(self):
        organism = {"canonical_name": "Mus musculus", "ncbi_taxonomy_id": 10090}
        disease = None
        data_type = {"canonical_name": "scRNAseq"}
        query = build_search_query(
            organism=organism,
            disease=disease,
            data_type=data_type
        )
        self.assertIn("organism:(Mus musculus)", query)
        self.assertIn("data_type:(scRNAseq)", query)
        self.assertNotIn("disease:", query)
        self.assertNotIn("samples:", query)
        self.assertNotIn("publication_date:", query)
    
    def test_build_search_query_special_case(self):
        organism = {
            "canonical_name": "Virus",
            "is_special_case": True,
            "expanded_terms": ["HIV", "SARS-CoV-2", "H1N1", "Ebola virus", "Zika virus"]
        }
        query = build_search_query(organism=organism)
        for virus in ["HIV", "SARS-CoV-2", "H1N1", "Ebola virus", "Zika virus"]:
            self.assertIn(virus, query)
        self.assertIn(" OR ", query)
    
    def test_parse_date_range_year(self):
        formatted_range = parse_date_range("2020-2023")
        self.assertEqual(formatted_range, "publication_date:[2020-01-01 TO 2023-12-31]")
    
    def test_parse_date_range_full(self):
        formatted_range = parse_date_range("2020-01-01:2023-12-31")
        self.assertEqual(formatted_range, "publication_date:[2020-01-01 TO 2023-12-31]")
    
    def test_parse_date_range_invalid(self):
        formatted_range = parse_date_range("last_5_years")
        self.assertEqual(formatted_range, "publication_date:last_5_years")
    
    def test_enhance_query_with_llm(self):
        enhanced_query = enhance_query_with_llm(
            organism="Human",
            disease="Cancer",
            data_type="RNAseq"
        )

        self.mock_llm_instance.expand_search_query.assert_called_once_with(
            "Human", "Cancer", "RNAseq"
        )

        expected_query = '(human OR "Homo sapiens") AND (cancer OR neoplasm OR tumor OR carcinoma) AND (RNAseq OR "RNA sequencing" OR transcriptomics)'
        self.assertEqual(enhanced_query, expected_query)
    
    def test_enhance_query_with_llm_partial(self):
        enhance_query_with_llm(organism="Mouse", disease=None, data_type=None)

        self.mock_llm_instance.expand_search_query.assert_called_once_with(
            "Mouse", None, None
        )
    
    def test_enhance_query_with_llm_empty(self):
        result = enhance_query_with_llm()
        self.assertEqual(result, "")
        self.mock_llm_instance.expand_search_query.assert_not_called()


if __name__ == "__main__":
    unittest.main()
