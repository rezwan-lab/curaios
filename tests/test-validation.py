"""
Unit tests for validation functionality.
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

from config.constants import InputType
from core.validation import (
    validate_input, 
    validate_organism, 
    validate_disease, 
    validate_data_type, 
    validate_generic
)
from utils.error_handling import ValidationError


class TestValidation(unittest.TestCase):
    
    def test_validate_input_none(self):
        with self.assertRaises(ValidationError):
            validate_input(None, InputType.ORGANISM.value)
    
    def test_validate_input_empty(self):
        with self.assertRaises(ValidationError):
            validate_input('', InputType.ORGANISM.value)
        with self.assertRaises(ValidationError):
            validate_input('   ', InputType.ORGANISM.value)
    
    def test_validate_organism_valid(self):
        self.assertEqual(validate_organism("human"), "human")
        self.assertEqual(validate_organism("Homo sapiens"), "Homo sapiens")
        self.assertEqual(validate_organism("e. coli"), "e. coli")
        self.assertEqual(validate_organism("C. elegans"), "C. elegans")
    
    def test_validate_organism_invalid(self):
        with self.assertRaises(ValidationError):
            validate_organism("h")

            validate_organism("human@!")
    
    def test_validate_organism_warning(self):
        self.assertEqual(validate_organism("bacteria"), "bacteria")
        self.assertEqual(validate_organism("virus"), "virus")
        self.assertEqual(validate_organism("cancer"), "cancer")
    
    def test_validate_disease_valid(self):
        self.assertEqual(validate_disease("alzheimer's disease"), "alzheimer's disease")
        self.assertEqual(validate_disease("diabetes"), "diabetes")
        self.assertEqual(validate_disease("breast cancer"), "breast cancer")
        self.assertEqual(validate_disease("COVID-19"), "COVID-19")
    
    def test_validate_disease_invalid(self):
        with self.assertRaises(ValidationError):
            validate_disease("a")
        self.assertEqual(validate_disease("flu@!"), "flu")
    
    def test_validate_disease_warning(self):
        self.assertEqual(validate_disease("human"), "human")
        self.assertEqual(validate_disease("bacteria"), "bacteria")
    
    def test_validate_data_type_valid(self):
        self.assertEqual(validate_data_type("RNAseq"), "RNAseq")
        self.assertEqual(validate_data_type("single cell RNA-seq"), "single cell RNA-seq")
        self.assertEqual(validate_data_type("microarray"), "microarray")
        self.assertEqual(validate_data_type("proteomics"), "proteomics")
    
    def test_validate_data_type_invalid(self):
        with self.assertRaises(ValidationError):
            validate_data_type("r")

        self.assertEqual(validate_data_type("RNA-seq@!"), "RNA-seq")
    
    def test_validate_data_type_conversion(self):
        self.assertEqual(validate_data_type("RNA"), "RNAseq")
        self.assertEqual(validate_data_type("scRNA"), "scRNAseq")
    
    def test_validate_generic(self):
        self.assertEqual(validate_generic("test input"), "test input")
        self.assertEqual(validate_generic("123"), "123")

        with self.assertRaises(ValidationError):
            validate_generic("a")
        
        self.assertEqual(validate_generic("test@input!"), "testinput")
    
    def test_validate_generic_sql_injection(self):
        with self.assertRaises(ValidationError):
            validate_generic("SELECT * FROM users")
        
        with self.assertRaises(ValidationError):
            validate_generic("DROP TABLE samples;")
        
        with self.assertRaises(ValidationError):
            validate_generic("1; DELETE FROM organisms--")


if __name__ == "__main__":
    unittest.main()
