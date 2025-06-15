"""
Routers for directing queries to appropriate domain experts in Diadochi.

This module provides various routing strategies including keyword-based,
embedding-based, classifier-based, and LLM-based routing.
"""

import re
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    SentenceTransformer = TfidfVectorizer = cosine_similarity = None

logger = logging.getLogger(__name__)


@dataclass 
class DomainDescription:
    """Description of a domain for routing purposes."""
    name: str
    description: str
    keywords: Set[str]
    examples: List[str]
    embedding: Optional[List[float]] = None


class Router(ABC):
    """Abstract base class for all routers."""
    
    def __init__(self, threshold: float = 0.5):
        """
        Initialize the router.
        
        Args:
            threshold: Minimum confidence threshold for routing
        """
        self.threshold = threshold
        self.domains: Dict[str, DomainDescription] = {}
    
    @abstractmethod
    async def route(self, query: str, available_models: List[str]) -> Optional[str]:
        """
        Route a query to the most appropriate model.
        
        Args:
            query: Query to route
            available_models: List of available model names
            
        Returns:
            Name of the selected model, or None if no suitable model found
        """
        pass
    
    @abstractmethod
    async def route_multiple(
        self, 
        query: str, 
        available_models: List[str], 
        k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Route a query to the k most appropriate models.
        
        Args:
            query: Query to route
            available_models: List of available model names
            k: Number of models to return
            
        Returns:
            List of (model_name, confidence_score) tuples
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
        Add a domain description.
        
        Args:
            name: Domain name
            description: Domain description
            keywords: Keywords associated with the domain
            examples: Example queries for the domain
        """
        self.domains[name] = DomainDescription(
            name=name,
            description=description,
            keywords=set(keywords or []),
            examples=examples or []
        )
        logger.info(f"Added domain '{name}' to router")


class KeywordRouter(Router):
    """Router based on keyword matching."""
    
    def __init__(self, threshold: float = 0.3, case_sensitive: bool = False):
        """
        Initialize the keyword router.
        
        Args:
            threshold: Minimum keyword match ratio for routing
            case_sensitive: Whether keyword matching is case sensitive
        """
        super().__init__(threshold)
        self.case_sensitive = case_sensitive
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for all domains."""
        self.patterns = {}
        for domain_name, domain in self.domains.items():
            if domain.keywords:
                flags = 0 if self.case_sensitive else re.IGNORECASE
                pattern = '|'.join(re.escape(keyword) for keyword in domain.keywords)
                self.patterns[domain_name] = re.compile(r'\b(?:' + pattern + r')\b', flags)
    
    def add_domain(
        self, 
        name: str, 
        description: str, 
        keywords: Optional[List[str]] = None,
        examples: Optional[List[str]] = None
    ) -> None:
        """Add a domain and compile its keyword patterns."""
        super().add_domain(name, description, keywords, examples)
        self._compile_patterns()
    
    async def route(self, query: str, available_models: List[str]) -> Optional[str]:
        """Route based on keyword matching."""
        scores = await self._calculate_scores(query, available_models)
        
        if not scores:
            return None
        
        best_model, best_score = max(scores.items(), key=lambda x: x[1])
        return best_model if best_score >= self.threshold else None
    
    async def route_multiple(
        self, 
        query: str, 
        available_models: List[str], 
        k: int = 3
    ) -> List[Tuple[str, float]]:
        """Route to multiple models based on keyword matching."""
        scores = await self._calculate_scores(query, available_models)
        
        if not scores:
            return []
        
        # Sort by score and return top k above threshold
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(model, score) for model, score in sorted_scores[:k] if score >= self.threshold]
    
    async def _calculate_scores(self, query: str, available_models: List[str]) -> Dict[str, float]:
        """Calculate keyword match scores for available models."""
        scores = {}
        
        for model in available_models:
            if model in self.domains and model in self.patterns:
                pattern = self.patterns[model]
                matches = pattern.findall(query)
                
                if matches:
                    # Score based on number of matches relative to total keywords
                    unique_matches = set(matches)
                    total_keywords = len(self.domains[model].keywords)
                    scores[model] = len(unique_matches) / total_keywords if total_keywords > 0 else 0
                else:
                    scores[model] = 0.0
        
        return scores


class EmbeddingRouter(Router):
    """Router based on embedding similarity."""
    
    def __init__(
        self, 
        threshold: float = 0.6, 
        embedding_model: Optional[str] = None,
        temperature: float = 1.0
    ):
        """
        Initialize the embedding router.
        
        Args:
            threshold: Minimum similarity threshold for routing
            embedding_model: Name of the embedding model to use
            temperature: Temperature for softmax normalization
        """
        super().__init__(threshold)
        self.temperature = temperature
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
        """Add a domain and compute its embedding."""
        super().add_domain(name, description, keywords, examples)
        
        if self.embedding_model:
            # Create a comprehensive text representation of the domain
            domain_text = f"{description}. "
            if keywords:
                domain_text += f"Keywords: {', '.join(keywords)}. "
            if examples:
                domain_text += f"Examples: {' '.join(examples)}"
            
            try:
                embedding = self.embedding_model.encode(domain_text)
                self.domains[name].embedding = embedding.tolist()
            except Exception as e:
                logger.error(f"Failed to compute embedding for domain '{name}': {e}")
    
    async def route(self, query: str, available_models: List[str]) -> Optional[str]:
        """Route based on embedding similarity."""
        if not self.embedding_model:
            logger.warning("No embedding model available for routing")
            return None
        
        scores = await self._calculate_scores(query, available_models)
        
        if not scores:
            return None
        
        best_model, best_score = max(scores.items(), key=lambda x: x[1])
        return best_model if best_score >= self.threshold else None
    
    async def route_multiple(
        self, 
        query: str, 
        available_models: List[str], 
        k: int = 3
    ) -> List[Tuple[str, float]]:
        """Route to multiple models based on embedding similarity."""
        scores = await self._calculate_scores(query, available_models)
        
        if not scores:
            return []
        
        # Apply softmax for better distribution
        score_values = np.array(list(scores.values()))
        if self.temperature != 1.0:
            score_values = score_values / self.temperature
        
        # Softmax normalization
        exp_scores = np.exp(score_values - np.max(score_values))
        softmax_scores = exp_scores / np.sum(exp_scores)
        
        # Create sorted list with softmax scores
        model_names = list(scores.keys())
        model_scores = [(model_names[i], float(softmax_scores[i])) for i in range(len(model_names))]
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k above threshold
        return [(model, score) for model, score in model_scores[:k] if score >= self.threshold]
    
    async def _calculate_scores(self, query: str, available_models: List[str]) -> Dict[str, float]:
        """Calculate embedding similarity scores for available models."""
        if not self.embedding_model:
            return {}
        
        try:
            # Get query embedding
            query_embedding = self.embedding_model.encode(query)
            scores = {}
            
            for model in available_models:
                if model in self.domains and self.domains[model].embedding:
                    domain_embedding = np.array(self.domains[model].embedding)
                    
                    # Calculate cosine similarity
                    similarity = np.dot(query_embedding, domain_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(domain_embedding)
                    )
                    scores[model] = float(similarity)
            
            return scores
        except Exception as e:
            logger.error(f"Error calculating embedding scores: {e}")
            return {}


class ClassifierRouter(Router):
    """Router based on a trained classifier."""
    
    def __init__(
        self, 
        threshold: float = 0.6,
        model_path: Optional[str] = None,
        vectorizer_path: Optional[str] = None
    ):
        """
        Initialize the classifier router.
        
        Args:
            threshold: Minimum prediction confidence for routing
            model_path: Path to the trained classifier model
            vectorizer_path: Path to the text vectorizer
        """
        super().__init__(threshold)
        self.classifier = None
        self.vectorizer = None
        self.label_to_domain = {}
        
        # Load classifier and vectorizer if paths provided
        if model_path and vectorizer_path:
            self._load_classifier(model_path, vectorizer_path)
    
    def _load_classifier(self, model_path: str, vectorizer_path: str):
        """Load the trained classifier and vectorizer."""
        try:
            import joblib
            self.classifier = joblib.load(model_path)
            self.vectorizer = joblib.load(vectorizer_path)
            logger.info("Loaded classifier and vectorizer successfully")
        except Exception as e:
            logger.error(f"Failed to load classifier: {e}")
    
    def train_classifier(self, training_data: List[Tuple[str, str]]):
        """
        Train a classifier on the provided data.
        
        Args:
            training_data: List of (query, domain) tuples
        """
        if not TfidfVectorizer:
            raise ImportError("scikit-learn is required for classifier training")
        
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import classification_report
            
            # Prepare data
            queries, domains = zip(*training_data)
            
            # Create vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Vectorize queries
            X = self.vectorizer.fit_transform(queries)
            y = list(domains)
            
            # Create label mapping
            unique_domains = list(set(domains))
            self.label_to_domain = {i: domain for i, domain in enumerate(unique_domains)}
            domain_to_label = {domain: i for i, domain in self.label_to_domain.items()}
            y_numeric = [domain_to_label[domain] for domain in y]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y_numeric, test_size=0.2, random_state=42, stratify=y_numeric
            )
            
            # Train classifier
            self.classifier = RandomForestClassifier(n_estimators=100, random_state=42)
            self.classifier.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.classifier.predict(X_test)
            test_domains = [self.label_to_domain[label] for label in y_test]
            pred_domains = [self.label_to_domain[label] for label in y_pred]
            
            logger.info("Classifier training completed")
            logger.info(f"Classification report:\n{classification_report(test_domains, pred_domains)}")
            
        except Exception as e:
            logger.error(f"Failed to train classifier: {e}")
            raise
    
    async def route(self, query: str, available_models: List[str]) -> Optional[str]:
        """Route based on classifier prediction."""
        if not self.classifier or not self.vectorizer:
            logger.warning("No classifier available for routing")
            return None
        
        scores = await self._calculate_scores(query, available_models)
        
        if not scores:
            return None
        
        best_model, best_score = max(scores.items(), key=lambda x: x[1])
        return best_model if best_score >= self.threshold else None
    
    async def route_multiple(
        self, 
        query: str, 
        available_models: List[str], 
        k: int = 3
    ) -> List[Tuple[str, float]]:
        """Route to multiple models based on classifier prediction."""
        scores = await self._calculate_scores(query, available_models)
        
        if not scores:
            return []
        
        # Sort by score and return top k above threshold
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(model, score) for model, score in sorted_scores[:k] if score >= self.threshold]
    
    async def _calculate_scores(self, query: str, available_models: List[str]) -> Dict[str, float]:
        """Calculate classifier prediction scores for available models."""
        if not self.classifier or not self.vectorizer:
            return {}
        
        try:
            # Vectorize query
            query_vector = self.vectorizer.transform([query])
            
            # Get prediction probabilities
            probabilities = self.classifier.predict_proba(query_vector)[0]
            
            # Map probabilities to available models
            scores = {}
            for i, prob in enumerate(probabilities):
                domain = self.label_to_domain.get(i)
                if domain and domain in available_models:
                    scores[domain] = float(prob)
            
            return scores
        except Exception as e:
            logger.error(f"Error calculating classifier scores: {e}")
            return {}


class LLMRouter(Router):
    """Router that uses an LLM to determine routing."""
    
    def __init__(
        self, 
        threshold: float = 0.6,
        router_model=None,
        prompt_template: Optional[str] = None
    ):
        """
        Initialize the LLM router.
        
        Args:
            threshold: Minimum confidence threshold for routing
            router_model: Model to use for routing decisions
            prompt_template: Template for routing prompts
        """
        super().__init__(threshold)
        self.router_model = router_model
        self.prompt_template = prompt_template or self._default_prompt_template()
    
    def _default_prompt_template(self) -> str:
        """Default prompt template for routing."""
        return """
You are a domain routing expert. Given a query and a list of available domains, determine which domain(s) are most relevant to answer the query.

Available domains:
{domains}

Query: {query}

For each domain, provide a relevance score from 0.0 to 1.0, where:
- 0.0 = completely irrelevant
- 0.5 = somewhat relevant  
- 1.0 = highly relevant

Respond in JSON format:
{
  "domain_scores": {
    "domain_name": score,
    ...
  },
  "reasoning": "Brief explanation of your scoring"
}
"""
    
    async def route(self, query: str, available_models: List[str]) -> Optional[str]:
        """Route using LLM analysis."""
        if not self.router_model:
            logger.warning("No router model available for LLM routing")
            return None
        
        scores = await self._calculate_scores(query, available_models)
        
        if not scores:
            return None
        
        best_model, best_score = max(scores.items(), key=lambda x: x[1])
        return best_model if best_score >= self.threshold else None
    
    async def route_multiple(
        self, 
        query: str, 
        available_models: List[str], 
        k: int = 3
    ) -> List[Tuple[str, float]]:
        """Route to multiple models using LLM analysis."""
        scores = await self._calculate_scores(query, available_models)
        
        if not scores:
            return []
        
        # Sort by score and return top k above threshold
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [(model, score) for model, score in sorted_scores[:k] if score >= self.threshold]
    
    async def _calculate_scores(self, query: str, available_models: List[str]) -> Dict[str, float]:
        """Calculate LLM-based routing scores."""
        if not self.router_model:
            return {}
        
        try:
            # Format domain descriptions
            domain_descriptions = []
            for model in available_models:
                if model in self.domains:
                    domain = self.domains[model]
                    desc = f"- {model}: {domain.description}"
                    if domain.keywords:
                        desc += f" (Keywords: {', '.join(list(domain.keywords)[:5])})"
                    domain_descriptions.append(desc)
            
            if not domain_descriptions:
                return {}
            
            # Create prompt
            prompt = self.prompt_template.format(
                domains="\n".join(domain_descriptions),
                query=query
            )
            
            # Get LLM response
            response = await self.router_model.generate(prompt)
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response.strip())
                domain_scores = result.get("domain_scores", {})
                
                # Filter to available models and validate scores
                scores = {}
                for model in available_models:
                    if model in domain_scores:
                        score = float(domain_scores[model])
                        if 0.0 <= score <= 1.0:
                            scores[model] = score
                
                return scores
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM routing response: {response}")
                return {}
        
        except Exception as e:
            logger.error(f"Error in LLM routing: {e}")
            return {}


def create_router(router_type: str, **kwargs) -> Router:
    """
    Factory function to create routers.
    
    Args:
        router_type: Type of router ("keyword", "embedding", "classifier", "llm")
        **kwargs: Router-specific parameters
        
    Returns:
        Router instance
    """
    router_map = {
        "keyword": KeywordRouter,
        "embedding": EmbeddingRouter,
        "classifier": ClassifierRouter,
        "llm": LLMRouter,
    }
    
    if router_type not in router_map:
        raise ValueError(f"Unsupported router type: {router_type}")
    
    return router_map[router_type](**kwargs) 