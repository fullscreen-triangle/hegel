"""
Confidence estimation utilities for Diadochi.

This module provides various strategies for estimating the confidence or relevance
of domain experts for specific queries.
"""

import logging
import asyncio
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
import re

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    SentenceTransformer = TfidfVectorizer = cosine_similarity = None

logger = logging.getLogger(__name__)


@dataclass
class DomainProfile:
    """Profile of a domain for confidence estimation."""
    name: str
    description: str
    keywords: Set[str]
    examples: List[str]
    embedding: Optional[List[float]] = None
    tfidf_features: Optional[Any] = None


class ConfidenceEstimator(ABC):
    """Abstract base class for confidence estimators."""
    
    def __init__(self):
        self.domain_profiles: Dict[str, DomainProfile] = {}
    
    @abstractmethod
    async def estimate_confidence(
        self, 
        query: str, 
        available_domains: List[str]
    ) -> Dict[str, float]:
        """
        Estimate confidence scores for available domains.
        
        Args:
            query: Input query
            available_domains: List of available domain names
            
        Returns:
            Dictionary mapping domain names to confidence scores (0.0 to 1.0)
        """
        pass
    
    def add_domain(
        self, 
        name: str, 
        description: str, 
        keywords: Optional[List[str]] = None,
        examples: Optional[List[str]] = None
    ) -> None:
        """
        Add a domain profile.
        
        Args:
            name: Domain name
            description: Domain description
            keywords: Keywords associated with the domain
            examples: Example queries for the domain
        """
        self.domain_profiles[name] = DomainProfile(
            name=name,
            description=description,
            keywords=set(keywords or []),
            examples=examples or []
        )
        logger.info(f"Added domain profile for '{name}'")


class KeywordConfidence(ConfidenceEstimator):
    """Confidence estimator based on keyword matching."""
    
    def __init__(self, case_sensitive: bool = False, boost_exact_matches: bool = True):
        """
        Initialize keyword confidence estimator.
        
        Args:
            case_sensitive: Whether keyword matching is case sensitive
            boost_exact_matches: Whether to boost scores for exact keyword matches
        """
        super().__init__()
        self.case_sensitive = case_sensitive
        self.boost_exact_matches = boost_exact_matches
        self._compile_patterns()
    
    def add_domain(
        self, 
        name: str, 
        description: str, 
        keywords: Optional[List[str]] = None,
        examples: Optional[List[str]] = None
    ) -> None:
        """Add domain and compile keyword patterns."""
        super().add_domain(name, description, keywords, examples)
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for all domains."""
        self.patterns = {}
        self.exact_patterns = {}
        
        for domain_name, profile in self.domain_profiles.items():
            if profile.keywords:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                
                # Pattern for partial matches
                pattern = '|'.join(re.escape(keyword) for keyword in profile.keywords)
                self.patterns[domain_name] = re.compile(r'(?:' + pattern + r')', flags)
                
                # Pattern for exact word matches
                exact_pattern = '|'.join(re.escape(keyword) for keyword in profile.keywords)
                self.exact_patterns[domain_name] = re.compile(r'\b(?:' + exact_pattern + r')\b', flags)
    
    async def estimate_confidence(
        self, 
        query: str, 
        available_domains: List[str]
    ) -> Dict[str, float]:
        """Estimate confidence based on keyword matching."""
        confidences = {}
        
        for domain in available_domains:
            if domain not in self.domain_profiles:
                confidences[domain] = 0.0
                continue
            
            profile = self.domain_profiles[domain]
            
            if not profile.keywords:
                confidences[domain] = 0.0
                continue
            
            # Count matches
            partial_matches = len(self.patterns[domain].findall(query)) if domain in self.patterns else 0
            exact_matches = len(self.exact_patterns[domain].findall(query)) if domain in self.exact_patterns else 0
            
            # Calculate confidence
            total_keywords = len(profile.keywords)
            
            if self.boost_exact_matches:
                # Weight exact matches more heavily
                score = (exact_matches * 2 + partial_matches) / (total_keywords * 2)
            else:
                score = partial_matches / total_keywords
            
            # Normalize to [0, 1]
            confidences[domain] = min(score, 1.0)
        
        return confidences


class EmbeddingConfidence(ConfidenceEstimator):
    """Confidence estimator based on embedding similarity."""
    
    def __init__(
        self, 
        embedding_model: Optional[str] = None,
        temperature: float = 1.0,
        similarity_metric: str = "cosine"
    ):
        """
        Initialize embedding confidence estimator.
        
        Args:
            embedding_model: Name of the embedding model to use
            temperature: Temperature for softmax normalization
            similarity_metric: Similarity metric to use ("cosine", "euclidean", "dot")
        """
        super().__init__()
        self.temperature = temperature
        self.similarity_metric = similarity_metric
        self.embedding_model = None
        
        if SentenceTransformer:
            try:
                model_name = embedding_model or 'all-MiniLM-L6-v2'
                self.embedding_model = SentenceTransformer(model_name)
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
    
    def add_domain(
        self, 
        name: str, 
        description: str, 
        keywords: Optional[List[str]] = None,
        examples: Optional[List[str]] = None
    ) -> None:
        """Add domain and compute its embedding."""
        super().add_domain(name, description, keywords, examples)
        
        if self.embedding_model:
            profile = self.domain_profiles[name]
            
            # Create comprehensive domain text
            domain_text = f"{description}. "
            if keywords:
                domain_text += f"Keywords: {', '.join(keywords)}. "
            if examples:
                domain_text += f"Examples: {' '.join(examples)}"
            
            try:
                embedding = self.embedding_model.encode(domain_text)
                profile.embedding = embedding.tolist()
            except Exception as e:
                logger.error(f"Failed to compute embedding for domain '{name}': {e}")
    
    async def estimate_confidence(
        self, 
        query: str, 
        available_domains: List[str]
    ) -> Dict[str, float]:
        """Estimate confidence based on embedding similarity."""
        if not self.embedding_model:
            logger.warning("No embedding model available")
            return {domain: 0.0 for domain in available_domains}
        
        confidences = {}
        
        try:
            # Get query embedding
            query_embedding = self.embedding_model.encode(query)
            
            similarities = []
            valid_domains = []
            
            for domain in available_domains:
                if domain not in self.domain_profiles:
                    confidences[domain] = 0.0
                    continue
                    
                profile = self.domain_profiles[domain]
                if not profile.embedding:
                    confidences[domain] = 0.0
                    continue
                
                # Calculate similarity
                domain_embedding = np.array(profile.embedding)
                
                if self.similarity_metric == "cosine":
                    similarity = np.dot(query_embedding, domain_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(domain_embedding)
                    )
                elif self.similarity_metric == "euclidean":
                    # Convert euclidean distance to similarity
                    distance = np.linalg.norm(query_embedding - domain_embedding)
                    similarity = 1.0 / (1.0 + distance)
                elif self.similarity_metric == "dot":
                    similarity = np.dot(query_embedding, domain_embedding)
                else:
                    raise ValueError(f"Unknown similarity metric: {self.similarity_metric}")
                
                similarities.append(similarity)
                valid_domains.append(domain)
            
            if similarities:
                # Apply softmax normalization
                similarities = np.array(similarities)
                if self.temperature != 1.0:
                    similarities = similarities / self.temperature
                
                # Softmax
                exp_similarities = np.exp(similarities - np.max(similarities))
                softmax_similarities = exp_similarities / np.sum(exp_similarities)
                
                # Map back to domains
                for i, domain in enumerate(valid_domains):
                    confidences[domain] = float(softmax_similarities[i])
        
        except Exception as e:
            logger.error(f"Error computing embedding confidences: {e}")
            return {domain: 0.0 for domain in available_domains}
        
        return confidences


class TFIDFConfidence(ConfidenceEstimator):
    """Confidence estimator based on TF-IDF similarity."""
    
    def __init__(self, max_features: int = 5000, ngram_range: tuple = (1, 2)):
        """
        Initialize TF-IDF confidence estimator.
        
        Args:
            max_features: Maximum number of features for TF-IDF
            ngram_range: N-gram range for TF-IDF
        """
        super().__init__()
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.vectorizer = None
        self.domain_vectors = {}
        
        if TfidfVectorizer:
            self.vectorizer = TfidfVectorizer(
                max_features=max_features,
                stop_words='english',
                ngram_range=ngram_range
            )
    
    def add_domain(
        self, 
        name: str, 
        description: str, 
        keywords: Optional[List[str]] = None,
        examples: Optional[List[str]] = None
    ) -> None:
        """Add domain and update TF-IDF features."""
        super().add_domain(name, description, keywords, examples)
        self._update_tfidf_features()
    
    def _update_tfidf_features(self):
        """Update TF-IDF features for all domains."""
        if not self.vectorizer or not self.domain_profiles:
            return
        
        try:
            # Collect all domain texts
            domain_texts = []
            domain_names = []
            
            for name, profile in self.domain_profiles.items():
                domain_text = f"{profile.description} "
                if profile.keywords:
                    domain_text += f"{' '.join(profile.keywords)} "
                if profile.examples:
                    domain_text += f"{' '.join(profile.examples)}"
                
                domain_texts.append(domain_text)
                domain_names.append(name)
            
            # Fit TF-IDF vectorizer
            tfidf_matrix = self.vectorizer.fit_transform(domain_texts)
            
            # Store domain vectors
            for i, name in enumerate(domain_names):
                self.domain_vectors[name] = tfidf_matrix[i]
                
        except Exception as e:
            logger.error(f"Error updating TF-IDF features: {e}")
    
    async def estimate_confidence(
        self, 
        query: str, 
        available_domains: List[str]
    ) -> Dict[str, float]:
        """Estimate confidence based on TF-IDF similarity."""
        if not self.vectorizer or not self.domain_vectors:
            logger.warning("TF-IDF not initialized")
            return {domain: 0.0 for domain in available_domains}
        
        confidences = {}
        
        try:
            # Vectorize query
            query_vector = self.vectorizer.transform([query])
            
            similarities = []
            valid_domains = []
            
            for domain in available_domains:
                if domain not in self.domain_vectors:
                    confidences[domain] = 0.0
                    continue
                
                # Calculate cosine similarity
                domain_vector = self.domain_vectors[domain]
                similarity = cosine_similarity(query_vector, domain_vector)[0][0]
                
                similarities.append(similarity)
                valid_domains.append(domain)
            
            if similarities:
                # Normalize similarities to [0, 1]
                max_sim = max(similarities)
                min_sim = min(similarities)
                
                if max_sim > min_sim:
                    for i, domain in enumerate(valid_domains):
                        normalized_sim = (similarities[i] - min_sim) / (max_sim - min_sim)
                        confidences[domain] = normalized_sim
                else:
                    # All similarities are equal
                    for domain in valid_domains:
                        confidences[domain] = 1.0 / len(valid_domains)
        
        except Exception as e:
            logger.error(f"Error computing TF-IDF confidences: {e}")
            return {domain: 0.0 for domain in available_domains}
        
        return confidences


class LLMConfidence(ConfidenceEstimator):
    """Confidence estimator that uses an LLM to assess relevance."""
    
    def __init__(
        self, 
        model,
        prompt_template: Optional[str] = None,
        max_domains_per_call: int = 5
    ):
        """
        Initialize LLM confidence estimator.
        
        Args:
            model: LLM model to use for confidence estimation
            prompt_template: Template for confidence estimation prompts
            max_domains_per_call: Maximum domains to evaluate in a single LLM call
        """
        super().__init__()
        self.model = model
        self.max_domains_per_call = max_domains_per_call
        self.prompt_template = prompt_template or self._default_prompt_template()
    
    def _default_prompt_template(self) -> str:
        """Default prompt template for LLM confidence estimation."""
        return """
You are an expert at determining domain relevance for queries. Given a query and a list of domains with their descriptions, rate how relevant each domain is for answering the query.

Query: {query}

Domains:
{domain_descriptions}

For each domain, provide a relevance score from 0.0 to 1.0, where:
- 0.0 = completely irrelevant
- 0.5 = somewhat relevant
- 1.0 = highly relevant

Respond in JSON format:
{{
  "scores": {{
    "domain_name": score,
    ...
  }},
  "reasoning": "Brief explanation of your scoring"
}}
"""
    
    async def estimate_confidence(
        self, 
        query: str, 
        available_domains: List[str]
    ) -> Dict[str, float]:
        """Estimate confidence using LLM analysis."""
        confidences = {}
        
        # Process domains in batches
        for i in range(0, len(available_domains), self.max_domains_per_call):
            batch_domains = available_domains[i:i + self.max_domains_per_call]
            batch_confidences = await self._estimate_batch_confidence(query, batch_domains)
            confidences.update(batch_confidences)
        
        return confidences
    
    async def _estimate_batch_confidence(
        self, 
        query: str, 
        domains: List[str]
    ) -> Dict[str, float]:
        """Estimate confidence for a batch of domains."""
        try:
            # Format domain descriptions
            domain_descriptions = []
            for domain in domains:
                if domain in self.domain_profiles:
                    profile = self.domain_profiles[domain]
                    desc = f"- {domain}: {profile.description}"
                    if profile.keywords:
                        desc += f" (Keywords: {', '.join(list(profile.keywords)[:5])})"
                    domain_descriptions.append(desc)
                else:
                    domain_descriptions.append(f"- {domain}: No description available")
            
            # Create prompt
            prompt = self.prompt_template.format(
                query=query,
                domain_descriptions="\n".join(domain_descriptions)
            )
            
            # Get LLM response
            response = await self.model.generate(prompt)
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response.strip())
                scores = result.get("scores", {})
                
                # Validate and return scores
                confidences = {}
                for domain in domains:
                    if domain in scores:
                        score = float(scores[domain])
                        confidences[domain] = max(0.0, min(1.0, score))  # Clamp to [0, 1]
                    else:
                        confidences[domain] = 0.0
                
                return confidences
            
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM confidence response: {response}")
                return {domain: 0.0 for domain in domains}
        
        except Exception as e:
            logger.error(f"Error in LLM confidence estimation: {e}")
            return {domain: 0.0 for domain in domains}


class HybridConfidence(ConfidenceEstimator):
    """Hybrid confidence estimator that combines multiple approaches."""
    
    def __init__(
        self, 
        estimators: List[ConfidenceEstimator],
        weights: Optional[List[float]] = None,
        combination_method: str = "weighted_average"
    ):
        """
        Initialize hybrid confidence estimator.
        
        Args:
            estimators: List of confidence estimators to combine
            weights: Weights for each estimator (defaults to equal weights)
            combination_method: Method for combining estimates ("weighted_average", "max", "vote")
        """
        super().__init__()
        self.estimators = estimators
        self.weights = weights or [1.0] * len(estimators)
        self.combination_method = combination_method
        
        if len(self.weights) != len(self.estimators):
            raise ValueError("Number of weights must match number of estimators")
        
        # Normalize weights
        total_weight = sum(self.weights)
        if total_weight > 0:
            self.weights = [w / total_weight for w in self.weights]
    
    def add_domain(
        self, 
        name: str, 
        description: str, 
        keywords: Optional[List[str]] = None,
        examples: Optional[List[str]] = None
    ) -> None:
        """Add domain to all estimators."""
        super().add_domain(name, description, keywords, examples)
        
        for estimator in self.estimators:
            estimator.add_domain(name, description, keywords, examples)
    
    async def estimate_confidence(
        self, 
        query: str, 
        available_domains: List[str]
    ) -> Dict[str, float]:
        """Estimate confidence by combining multiple estimators."""
        # Get confidence estimates from all estimators
        all_estimates = []
        
        for estimator in self.estimators:
            try:
                estimates = await estimator.estimate_confidence(query, available_domains)
                all_estimates.append(estimates)
            except Exception as e:
                logger.error(f"Error from estimator {type(estimator).__name__}: {e}")
                # Add zero estimates for failed estimator
                all_estimates.append({domain: 0.0 for domain in available_domains})
        
        # Combine estimates
        if self.combination_method == "weighted_average":
            return self._weighted_average_combination(all_estimates, available_domains)
        elif self.combination_method == "max":
            return self._max_combination(all_estimates, available_domains)
        elif self.combination_method == "vote":
            return self._vote_combination(all_estimates, available_domains)
        else:
            raise ValueError(f"Unknown combination method: {self.combination_method}")
    
    def _weighted_average_combination(
        self, 
        all_estimates: List[Dict[str, float]], 
        available_domains: List[str]
    ) -> Dict[str, float]:
        """Combine estimates using weighted average."""
        combined = {}
        
        for domain in available_domains:
            weighted_sum = 0.0
            for i, estimates in enumerate(all_estimates):
                weighted_sum += estimates.get(domain, 0.0) * self.weights[i]
            
            combined[domain] = weighted_sum
        
        return combined
    
    def _max_combination(
        self, 
        all_estimates: List[Dict[str, float]], 
        available_domains: List[str]
    ) -> Dict[str, float]:
        """Combine estimates using maximum."""
        combined = {}
        
        for domain in available_domains:
            max_confidence = 0.0
            for estimates in all_estimates:
                max_confidence = max(max_confidence, estimates.get(domain, 0.0))
            
            combined[domain] = max_confidence
        
        return combined
    
    def _vote_combination(
        self, 
        all_estimates: List[Dict[str, float]], 
        available_domains: List[str],
        vote_threshold: float = 0.5
    ) -> Dict[str, float]:
        """Combine estimates using voting (binary relevance)."""
        combined = {}
        
        for domain in available_domains:
            votes = 0
            for estimates in all_estimates:
                if estimates.get(domain, 0.0) >= vote_threshold:
                    votes += 1
            
            # Convert votes to confidence
            combined[domain] = votes / len(all_estimates) if all_estimates else 0.0
        
        return combined


def create_confidence_estimator(estimator_type: str, **kwargs) -> ConfidenceEstimator:
    """
    Factory function to create confidence estimators.
    
    Args:
        estimator_type: Type of estimator ("keyword", "embedding", "tfidf", "llm", "hybrid")
        **kwargs: Estimator-specific parameters
        
    Returns:
        ConfidenceEstimator instance
    """
    estimator_map = {
        "keyword": KeywordConfidence,
        "embedding": EmbeddingConfidence,
        "tfidf": TFIDFConfidence,
        "llm": LLMConfidence,
        "hybrid": HybridConfidence,
    }
    
    if estimator_type not in estimator_map:
        raise ValueError(f"Unsupported estimator type: {estimator_type}")
    
    return estimator_map[estimator_type](**kwargs) 