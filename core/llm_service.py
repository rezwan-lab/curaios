"""
Interface for LLM operations providing semantic understanding and matching.
Supports multiple LLM backends with consistent interface.

CurAIos - Biological Data Curator Project Setup Script
Curaios is an AI-native metadata curation engine.
It transforms messy biomedical inputs into structured and normalized forms using LLMs.
Author: Rezwanuzzaman Laskar
Date: 2025
GitHub: https://github.com/rezwan-lab

"""

import json
import logging
import os
import time
from typing import Dict, List, Any, Optional, Tuple, Union

import requests
import numpy as np

from config.settings import get_settings
from config.constants import LLM_PROMPTS
from utils.error_handling import LLMError, APIError

logger = logging.getLogger(__name__)


class LLMService:
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.llm_api_key
        self.model = self.settings.llm_model
        self.embedding_model = self.settings.llm_embedding_model
        self.temperature = self.settings.llm_temperature
        self.max_tokens = self.settings.llm_max_tokens
        
        self.provider = self.model.split('/')[0] if '/' in self.model else "openai"
    
    def generate_completion(self, prompt: str, temperature: Optional[float] = None) -> str:
        """
        Generate text completion from LLM.
        Args:
            prompt: The input prompt text
            temperature: Optional override for temperature parameter
        Returns:Generated text response
        Raises:LLMError: If there's an error communicating with the LLM API
        """
        if not self.api_key:
            logger.warning("LLM API key not set. Using fallback methods.")
            return ""
            
        temp = temperature if temperature is not None else self.temperature
        
        try:
            if self.api_key.startswith("sk-or-"):
                return self._openrouter_completion(prompt, temp)
            elif self.provider == "openai":
                return self._openai_completion(prompt, temp)
            elif self.provider == "anthropic":
                return self._anthropic_completion(prompt, temp)
            else:
                logger.warning(f"Unsupported LLM provider: {self.provider}. Using OpenRouter as fallback.")
                return self._openrouter_completion(prompt, temp)
                
        except Exception as e:
            logger.error(f"Error generating LLM completion: {e}", exc_info=True)
            raise LLMError(f"Failed to generate text: {e}")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        Args:texts: List of text strings to embed
        Returns:List of embedding vectors
        Raises:LLMError: If there's an error communicating with the embedding API
        """
        if not self.api_key:
            logger.warning("LLM API key not set. Using fallback methods.")
            return [np.zeros(1536).tolist() for _ in texts]  # Return dummy embeddings
        
        try:
            if "openai" in self.embedding_model:
                return self._openai_embeddings(texts)
            else:
                logger.warning(f"Unsupported embedding model: {self.embedding_model}. Using OpenAI as fallback.")
                return self._openai_embeddings(texts)
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}", exc_info=True)
            raise LLMError(f"Failed to generate embeddings: {e}")
    
    def semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts using embeddings.
        Args:
            text1: First text
            text2: Second text
        Returns:Cosine similarity score between 0 and 1
        """
        try:
            embeddings = self.generate_embeddings([text1, text2])
            return self._cosine_similarity(embeddings[0], embeddings[1])
        except Exception as e:
            logger.warning(f"Error calculating semantic similarity: {e}. Falling back to simpler methods.")
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
                
            overlap = len(words1.intersection(words2))
            return overlap / max(len(words1), len(words2))
    
    def validate_entity(self, input_text: str, entity_type: str) -> Dict[str, Any]:
        """
        Use LLM to validate and normalize an entity.
        Args:
            input_text: The user input to validate
            entity_type: Type of entity ('organism', 'disease', 'data_type')
        Returns:Dictionary with validated entity information
        """
        prompt_key = f"{entity_type}_validation"
        if prompt_key not in LLM_PROMPTS:
            raise ValueError(f"No prompt template found for entity type: {entity_type}")
            
        prompt = LLM_PROMPTS[prompt_key].format(input=input_text)
        
        try:
            response = self.generate_completion(prompt)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Error validating {entity_type} entity: {e}", exc_info=True)
            return {
                "canonical_name": input_text.capitalize(),
                "confidence": 0.5,
                "alternatives": []
            }
    
    def expand_search_query(self, organism=None, disease=None, data_type=None) -> str:
        """
        Use LLM to expand search query with relevant synonyms and related terms.
        Args:
            organism: Normalized organism name (optional)
            disease: Normalized disease name (optional)
            data_type: Normalized data type (optional)
        Returns:Expanded search query string
        """
        if not self.api_key:
            logger.warning("LLM API key not set. Constructing basic query without expansion.")
            return self._construct_basic_query(organism, disease, data_type)
        if not (organism or disease or data_type):
            logger.warning("No inputs provided for query expansion.")
            return ""
        prompt = LLM_PROMPTS.get("query_expansion", "Expand the following search terms: organism: {organism}, disease: {disease}, data_type: {data_type}")
        formatted_prompt = prompt.format(
            organism=organism or "Not specified",
            disease=disease or "Not specified",
            data_type=data_type or "Not specified"
        )
        
        try:
            response = self.generate_completion(formatted_prompt)
            try:
                parsed = self._parse_json_response(response)
                expanded_query = parsed.get("query", "")
                logger.info(f"Successfully expanded query: {expanded_query}")
                return expanded_query if expanded_query else self._construct_basic_query(organism, disease, data_type)
            except Exception as parse_error:
                logger.error(f"Error parsing LLM query expansion response: {parse_error}", exc_info=True)
                if "query:" in response.lower():
                    query_part = response.lower().split("query:", 1)[1].strip()
                    if "\n" in query_part:
                        query_part = query_part.split("\n", 1)[0].strip()
                    return query_part
                
                return self._construct_basic_query(organism, disease, data_type)
                
        except Exception as e:
            logger.error(f"Error expanding search query with LLM: {e}", exc_info=True)
            return self._construct_basic_query(organism, disease, data_type)
            
    def _construct_basic_query(self, organism=None, disease=None, data_type=None) -> str:
        """
        Construct a basic search query without LLM expansion.
        Args:
            organism: Normalized organism name (optional)
            disease: Normalized disease name (optional)
            data_type: Normalized data type (optional)
        Returns:Basic search query string
        """
        parts = []
        
        if organism:
            parts.append(f"organism:({organism})")
        
        if disease:
            parts.append(f"disease:({disease})")
            
        if data_type:
            parts.append(f"data_type:({data_type})")
            
        return " AND ".join(parts) if parts else ""
    
    def _openai_completion(self, prompt: str, temperature: float) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.model.replace("openai/", ""),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            raise APIError(f"OpenAI API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _anthropic_completion(self, prompt: str, temperature: float) -> str:
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": self.model.replace("anthropic/", ""),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            raise APIError(f"Anthropic API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return result["content"][0]["text"]
    
    def _openrouter_completion(self, prompt: str, temperature: float) -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://example.com"  # Replace with actual domain
        }
        
        data = {
            "model": self.model,  # Or hard-code "deepseek/deepseek-chat"
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": self.max_tokens
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        
        if response.status_code != 200:
            raise APIError(f"OpenRouter API error: {response.status_code} - {response.text}")
            
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        url = "https://api.openai.com/v1/embeddings"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.embedding_model.replace("openai/", ""),
            "input": texts
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            raise APIError(f"OpenAI Embeddings API error: {response.status_code} - {response.text}")
            
        result = response.json()
        sorted_data = sorted(result["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2:
            return 0.0
            
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                if "```json" in response and "```" in response.split("```json", 1)[1]:
                    json_str = response.split("```json", 1)[1].split("```", 1)[0]
                    return json.loads(json_str)
                
                elif "{" in response and "}" in response:
                    start_idx = response.find("{")
                    end_idx = response.rfind("}") + 1
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)
                
                else:
                    logger.warning(f"Could not extract JSON from response: {response}")
                    return {}
                    
            except Exception as e:
                logger.error(f"Error parsing LLM response as JSON: {e}", exc_info=True)
                return {}


_llm_service = None

def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service