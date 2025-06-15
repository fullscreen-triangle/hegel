"""
Core model interfaces and implementations for Diadochi.

This module provides the base Model interface and implementations for various
LLM providers including Ollama, OpenAI, Anthropic, and HuggingFace.
"""

import os
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import logging

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import ollama
except ImportError:
    ollama = None

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
except ImportError:
    AutoTokenizer = AutoModelForCausalLM = pipeline = torch = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for model instances."""
    name: str
    engine: str
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 30
    extra_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


class Model(ABC):
    """Abstract base class for all models."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.name = config.name
        self._embedding_model = None
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the model."""
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response to the given prompt."""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for the given text."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model is available and properly configured."""
        pass
    
    def get_embedding_model(self):
        """Get or create the embedding model."""
        if self._embedding_model is None and SentenceTransformer is not None:
            try:
                self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
        return self._embedding_model


class OllamaModel(Model):
    """Ollama model implementation."""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if not ollama:
            raise ImportError("ollama package is required for OllamaModel")
        self.client = ollama.Client(host=config.base_url or "http://localhost:11434")
    
    @property
    def model_name(self) -> str:
        return self.config.model_name
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response using Ollama."""
        try:
            options = {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
                **self.config.extra_params,
                **kwargs
            }
            
            response = self.client.generate(
                model=self.config.model_name,
                prompt=prompt,
                options=options
            )
            
            return response.get("response", "")
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using Ollama or fallback to sentence transformers."""
        try:
            # Try Ollama embeddings first
            response = self.client.embeddings(
                model=self.config.model_name,
                prompt=text
            )
            return response.get("embedding", [])
        except Exception as e:
            # Fallback to sentence transformers
            logger.warning(f"Ollama embeddings failed, using fallback: {e}")
            embedding_model = self.get_embedding_model()
            if embedding_model:
                return embedding_model.encode(text).tolist()
            else:
                raise RuntimeError("No embedding model available")
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            self.client.list()
            return True
        except Exception:
            return False


class OpenAIModel(Model):
    """OpenAI model implementation."""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if not openai:
            raise ImportError("openai package is required for OpenAIModel")
        
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key or os.getenv("OPENAI_API_KEY"),
            base_url=config.base_url
        )
    
    @property
    def model_name(self) -> str:
        return self.config.model_name
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response using OpenAI."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                **{k: v for k, v in self.config.extra_params.items() if k not in ["temperature", "max_tokens"]},
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            )
            
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI."""
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI embeddings failed, using fallback: {e}")
            embedding_model = self.get_embedding_model()
            if embedding_model:
                return embedding_model.encode(text).tolist()
            else:
                raise RuntimeError("No embedding model available")
    
    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        try:
            # Simple check - try to list models
            return self.client.api_key is not None
        except Exception:
            return False


class AnthropicModel(Model):
    """Anthropic model implementation."""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if not anthropic:
            raise ImportError("anthropic package is required for AnthropicModel")
        
        self.client = anthropic.AsyncAnthropic(
            api_key=config.api_key or os.getenv("ANTHROPIC_API_KEY"),
            base_url=config.base_url
        )
    
    @property
    def model_name(self) -> str:
        return self.config.model_name
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response using Anthropic."""
        try:
            response = await self.client.messages.create(
                model=self.config.model_name,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                messages=[{"role": "user", "content": prompt}],
                **{k: v for k, v in self.config.extra_params.items() if k not in ["temperature", "max_tokens"]},
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            )
            
            return response.content[0].text if response.content else ""
        except Exception as e:
            logger.error(f"Error generating response from Anthropic: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using sentence transformers (Anthropic doesn't provide embeddings)."""
        embedding_model = self.get_embedding_model()
        if embedding_model:
            return embedding_model.encode(text).tolist()
        else:
            raise RuntimeError("No embedding model available")
    
    def is_available(self) -> bool:
        """Check if Anthropic is available."""
        try:
            return self.client.api_key is not None
        except Exception:
            return False


class HuggingFaceModel(Model):
    """HuggingFace model implementation."""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        if not (AutoTokenizer and AutoModelForCausalLM and pipeline):
            raise ImportError("transformers package is required for HuggingFaceModel")
        
        self.device = "cuda" if torch and torch.cuda.is_available() else "cpu"
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(config.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                config.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                **config.extra_params
            )
            
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {e}")
            raise
    
    @property
    def model_name(self) -> str:
        return self.config.model_name
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response using HuggingFace."""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _generate():
                outputs = self.generator(
                    prompt,
                    max_new_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    **{k: v for k, v in self.config.extra_params.items() if k not in ["temperature", "max_tokens"]},
                    **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
                )
                
                generated_text = outputs[0]["generated_text"]
                # Remove the original prompt from the response
                if generated_text.startswith(prompt):
                    generated_text = generated_text[len(prompt):].strip()
                
                return generated_text
            
            return await loop.run_in_executor(None, _generate)
        except Exception as e:
            logger.error(f"Error generating response from HuggingFace: {e}")
            raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using sentence transformers."""
        embedding_model = self.get_embedding_model()
        if embedding_model:
            return embedding_model.encode(text).tolist()
        else:
            raise RuntimeError("No embedding model available")
    
    def is_available(self) -> bool:
        """Check if HuggingFace model is available."""
        try:
            return self.model is not None and self.tokenizer is not None
        except Exception:
            return False


def create_model(config: ModelConfig) -> Model:
    """Factory function to create models based on configuration."""
    engine_map = {
        "ollama": OllamaModel,
        "openai": OpenAIModel,
        "anthropic": AnthropicModel,
        "huggingface": HuggingFaceModel,
    }
    
    if config.engine not in engine_map:
        raise ValueError(f"Unsupported engine: {config.engine}")
    
    return engine_map[config.engine](config) 