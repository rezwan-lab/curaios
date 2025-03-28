"""
Unit tests for normalization functionality.
Curaios - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.constants import InputType
from core.normalization import normalize_input, clean_input, normalize_organism, normalize_disease, normalize_data_type
from core.validation import validate_input
from utils.error_handling import ValidationError, NormalizationError


class TestNormalization(unittest.TestCase):
    
    def setUp(self):
        self.llm_patcher = patch('core.llm_service.get_llm_service')
        self.mock_llm = self.llm_patcher.start()

        self.mock_llm_instance = MagicMock()
        self.mock_llm.return_value = self.mock_llm_instance

        self.mock_llm_instance.validate_entity.return_value = {
            "canonical_name": "Test Entity",
            "confidence": 0.9,
            "alternatives": ["Test", "Entity"]
        }
    
    def tearDown(self):
        self.llm_patcher.stop()
    
    def test_clean_input(self):
        self.assertEqual(clean_input("  human  "), "human")
        self.assertEqual(clean_input("E. coli"), "E. coli")
        self.assertEqual(clean_input("Alzheimer's"), "Alzheimers")
        self.assertEqual(clean_input("RNA-seq"), "RNA-seq")
    
    def test_validate_input_empty(self):
        with self.assertRaises(ValidationError):
            validate_input("", InputType.ORGANISM.value)
    
    def test_validate_input_organism(self):
        self.assertEqual(validate_input("human", InputType.ORGANISM.value), "human")
        self.assertEqual(validate_input("  Human  ", InputType.ORGANISM.value), "Human")

        with self.assertRaises(ValidationError):
            validate_input("h", InputType.ORGANISM.value)
    
    def test_validate_input_disease(self):
        self.assertEqual(validate_input("Alzheimer's disease", InputType.DISEASE.value), "Alzheimer's disease")
        self.assertEqual(validate_input("  Diabetes  ", InputType.DISEASE.value), "Diabetes")
        with self.assertRaises(ValidationError):
            validate_input("d", InputType.DISEASE.value)
    
    @patch('core.normalization.query_ncbi_taxonomy')
    def test_normalize_organism_local(self, mock_query_ncbi):
        mock_query_ncbi.return_value = {}
        result = normalize_organism("human")
        self.assertEqual(result["canonical_name"], "Homo sapiens")
        self.assertEqual(result["ncbi_taxonomy_id"], 9606)
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(result["source"], "local_mapping")
        mock_query_ncbi.assert_not_called()
    
    @patch('core.normalization.query_ncbi_taxonomy')
    def test_normalize_organism_ncbi(self, mock_query_ncbi):
        mock_query_ncbi.return_value = {
            "canonical_name": "Canis lupus familiaris",
            "ncbi_taxonomy_id": 9615,
            "confidence": 0.95,
            "alternatives": ["Dog", "Domestic dog"]
        }
        result = normalize_organism("dog")
        self.assertEqual(result["canonical_name"], "Canis lupus familiaris")
        self.assertEqual(result["ncbi_taxonomy_id"], 9615)
        self.assertEqual(result["source"], "ncbi_taxonomy")

        mock_query_ncbi.assert_called_once_with("dog")
    
    @patch('core.normalization.query_ncbi_taxonomy')
    def test_normalize_organism_llm_fallback(self, mock_query_ncbi):
        mock_query_ncbi.return_value = {}
    
        self.mock_llm_instance.validate_entity.return_value = {
            "canonical_name": "Felis catus",
            "confidence": 0.85,
            "alternatives": ["Cat", "Domestic cat"]
        }

        result = normalize_organism("kitty")
        
        self.assertEqual(result["canonical_name"], "Felis catus")
        self.assertEqual(result["source"], "llm")

        mock_query_ncbi.assert_called_once_with("kitty")
        self.mock_llm_instance.validate_entity.assert_called_once_with("kitty", "organism")
    
    @patch('core.normalization.query_ncbi_mesh')
    def test_normalize_disease_local(self, mock_query_mesh):
        mock_query_mesh.return_value = {}
        result = normalize_disease("alzheimer's")
        
        self.assertEqual(result["canonical_name"], "Alzheimer's Disease")
        self.assertEqual(result["mesh_id"], "D000544")
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(result["source"], "local_mapping")
        
        mock_query_mesh.assert_not_called()
    
    def test_normalize_data_type(self):
        result = normalize_data_type("rnaseq")
        self.assertEqual(result["canonical_name"], "RNAseq")
        self.assertEqual(result["confidence"], 1.0)
        self.assertEqual(result["source"], "local_mapping")
        
        result = normalize_data_type("single cell")
        self.assertEqual(result["canonical_name"], "scRNAseq")
        
        self.mock_llm_instance.validate_entity.return_value = {
            "canonical_name": "Spatial Transcriptomics",
            "confidence": 0.8,
            "alternatives": ["Spatial RNA-seq", "ST-seq"]
        }
        
        result = normalize_data_type("spatial expression")
        self.assertEqual(result["canonical_name"], "Spatial Transcriptomics")
        self.assertEqual(result["source"], "llm")


if __name__ == "__main__":
    unittest.main()
