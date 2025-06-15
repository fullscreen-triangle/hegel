"""
Chains for sequential processing through multiple domain experts in Diadochi.

This module provides chain implementations that pass queries through multiple
domain experts in sequence, with each expert building on previous insights.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from .models import Model

logger = logging.getLogger(__name__)


@dataclass
class ChainContext:
    """Context object that flows through the chain."""
    query: str
    responses: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def add_response(self, response: str, model_name: str):
        """Add a response to the context."""
        self.responses.append(response)
        self.metadata[f"response_{len(self.responses)-1}"] = response
        self.metadata[model_name] = response
    
    def get_previous_response(self) -> Optional[str]:
        """Get the most recent response."""
        return self.responses[-1] if self.responses else None
    
    def get_all_responses(self) -> List[str]:
        """Get all responses in order."""
        return self.responses.copy()


class Chain:
    """Chain multiple models sequentially."""
    
    def __init__(
        self, 
        models: List[Union[Model, str]], 
        prompt_templates: Optional[Dict[str, str]] = None,
        max_context_length: Optional[int] = None,
        stop_on_error: bool = True
    ):
        """
        Initialize the chain.
        
        Args:
            models: List of models or model names to chain
            prompt_templates: Templates for formatting prompts for each model
            max_context_length: Maximum context length before truncation
            stop_on_error: Whether to stop the chain if a model fails
        """
        self.models = models
        self.prompt_templates = prompt_templates or {}
        self.max_context_length = max_context_length
        self.stop_on_error = stop_on_error
        
        # Default prompt templates
        self._default_templates = {
            "first": "{query}",
            "middle": """Previous analysis: {prev_response}

Original query: {query}

Provide your additional insights and analysis.""",
            "last": """Previous analyses:
{all_responses}

Original query: {query}

Synthesize the above analyses into a comprehensive, integrated response."""
        }
    
    async def generate(self, query: str, **kwargs) -> str:
        """
        Generate a response by chaining models.
        
        Args:
            query: Input query
            **kwargs: Additional parameters for generation
            
        Returns:
            Final response from the chain
        """
        context = ChainContext(query=query, responses=[], metadata={})
        
        for i, model in enumerate(self.models):
            try:
                # Get model instance
                if isinstance(model, str):
                    # Assume it's a model name that will be resolved elsewhere
                    model_name = model
                    # For now, skip string models - they should be resolved by the caller
                    logger.warning(f"String model '{model}' encountered, skipping")
                    continue
                else:
                    model_name = getattr(model, 'name', f'model_{i}')
                
                # Format prompt
                prompt = self._format_prompt(context, model_name, i, len(self.models))
                
                # Truncate if needed
                if self.max_context_length and len(prompt) > self.max_context_length:
                    prompt = self._truncate_prompt(prompt, self.max_context_length)
                
                # Generate response
                response = await model.generate(prompt, **kwargs)
                
                # Add to context
                context.add_response(response, model_name)
                
                logger.debug(f"Chain step {i+1}/{len(self.models)} completed for model '{model_name}'")
                
            except Exception as e:
                logger.error(f"Error in chain step {i+1} with model '{model_name}': {e}")
                
                if self.stop_on_error:
                    raise
                else:
                    # Add error placeholder and continue
                    error_response = f"[Error in {model_name}: {str(e)}]"
                    context.add_response(error_response, model_name)
        
        # Return the final response
        if context.responses:
            return context.responses[-1]
        else:
            raise RuntimeError("Chain produced no responses")
    
    def _format_prompt(self, context: ChainContext, model_name: str, step: int, total_steps: int) -> str:
        """Format the prompt for a specific model in the chain."""
        # Check for model-specific template
        if model_name in self.prompt_templates:
            template = self.prompt_templates[model_name]
        else:
            # Use position-based default templates
            if step == 0:
                template = self._default_templates["first"]
            elif step == total_steps - 1:
                template = self._default_templates["last"]
            else:
                template = self._default_templates["middle"]
        
        # Format the template
        try:
            # Prepare format arguments
            format_args = {
                "query": context.query,
                "prev_response": context.get_previous_response() or "",
                "responses": context.get_all_responses(),
                "all_responses": self._format_all_responses(context),
                **context.metadata
            }
            
            return template.format(**format_args)
        except KeyError as e:
            logger.warning(f"Template formatting error for {model_name}: {e}")
            # Fallback to simple format
            if context.responses:
                return f"Previous: {context.get_previous_response()}\nQuery: {context.query}"
            else:
                return context.query
    
    def _format_all_responses(self, context: ChainContext) -> str:
        """Format all previous responses for inclusion in prompts."""
        if not context.responses:
            return "None"
        
        formatted = []
        for i, response in enumerate(context.responses):
            formatted.append(f"Analysis {i+1}:\n{response}")
        
        return "\n\n".join(formatted)
    
    def _truncate_prompt(self, prompt: str, max_length: int) -> str:
        """Truncate prompt if it exceeds maximum length."""
        if len(prompt) <= max_length:
            return prompt
        
        # Simple truncation - could be improved with more sophisticated methods
        logger.warning(f"Truncating prompt from {len(prompt)} to {max_length} characters")
        return prompt[:max_length-100] + "\n\n[Content truncated]\n\nOriginal query: " + prompt.split("Original query:")[-1] if "Original query:" in prompt else prompt[:max_length]


class SummarizingChain(Chain):
    """Chain that automatically summarizes intermediate responses to manage context length."""
    
    def __init__(
        self,
        models: List[Union[Model, str]],
        summarizer: Optional[Model] = None,
        summary_threshold: int = 2000,
        summary_target_length: int = 500,
        prompt_templates: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Initialize the summarizing chain.
        
        Args:
            models: List of models to chain
            summarizer: Model to use for summarization (defaults to last model)
            summary_threshold: Length threshold to trigger summarization
            summary_target_length: Target length for summaries
            prompt_templates: Custom prompt templates
            **kwargs: Additional arguments for Chain
        """
        super().__init__(models, prompt_templates, **kwargs)
        self.summarizer = summarizer
        self.summary_threshold = summary_threshold
        self.summary_target_length = summary_target_length
        
        self.summary_template = """
Summarize the following analysis concisely while preserving all key insights and important details:

{content}

Summary (target length: ~{target_length} characters):
"""
    
    async def generate(self, query: str, **kwargs) -> str:
        """Generate response with automatic summarization of intermediate responses."""
        context = ChainContext(query=query, responses=[], metadata={})
        
        for i, model in enumerate(self.models):
            try:
                # Get model instance
                if isinstance(model, str):
                    model_name = model
                    logger.warning(f"String model '{model}' encountered, skipping")
                    continue
                else:
                    model_name = getattr(model, 'name', f'model_{i}')
                
                # Check if we need to summarize previous responses
                if i > 0 and self._should_summarize(context):
                    await self._summarize_context(context, **kwargs)
                
                # Format prompt
                prompt = self._format_prompt(context, model_name, i, len(self.models))
                
                # Generate response
                response = await model.generate(prompt, **kwargs)
                
                # Add to context
                context.add_response(response, model_name)
                
                logger.debug(f"Summarizing chain step {i+1}/{len(self.models)} completed")
                
            except Exception as e:
                logger.error(f"Error in summarizing chain step {i+1}: {e}")
                
                if self.stop_on_error:
                    raise
                else:
                    error_response = f"[Error in {model_name}: {str(e)}]"
                    context.add_response(error_response, model_name)
        
        return context.responses[-1] if context.responses else ""
    
    def _should_summarize(self, context: ChainContext) -> bool:
        """Determine if context should be summarized."""
        if not context.responses:
            return False
        
        # Check total length of responses
        total_length = sum(len(response) for response in context.responses)
        return total_length > self.summary_threshold
    
    async def _summarize_context(self, context: ChainContext, **kwargs):
        """Summarize the context to reduce length."""
        if not context.responses:
            return
        
        # Use the summarizer model (or the last model in the chain)
        summarizer = self.summarizer
        if summarizer is None and self.models:
            # Use the last model that's not a string
            for model in reversed(self.models):
                if not isinstance(model, str):
                    summarizer = model
                    break
        
        if summarizer is None:
            logger.warning("No summarizer available, skipping summarization")
            return
        
        try:
            # Combine all responses
            combined_content = self._format_all_responses(context)
            
            # Create summarization prompt
            summary_prompt = self.summary_template.format(
                content=combined_content,
                target_length=self.summary_target_length
            )
            
            # Generate summary
            summary = await summarizer.generate(summary_prompt, **kwargs)
            
            # Replace all responses with the summary
            context.responses = [summary]
            context.metadata = {"query": context.query, "summarized": True}
            context.metadata["response_0"] = summary
            
            logger.info(f"Summarized {len(context.responses)} responses into {len(summary)} characters")
            
        except Exception as e:
            logger.error(f"Failed to summarize context: {e}")
            # Don't fail the chain, just continue without summarization


class ConditionalChain(Chain):
    """Chain that can branch based on conditions or routing logic."""
    
    def __init__(
        self,
        models: List[Union[Model, str]],
        conditions: Optional[Dict[str, callable]] = None,
        branches: Optional[Dict[str, List[Union[Model, str]]]] = None,
        **kwargs
    ):
        """
        Initialize the conditional chain.
        
        Args:
            models: Default sequence of models
            conditions: Functions that determine branching (query, context) -> branch_name
            branches: Alternative model sequences for different branches
            **kwargs: Additional arguments for Chain
        """
        super().__init__(models, **kwargs)
        self.conditions = conditions or {}
        self.branches = branches or {}
    
    async def generate(self, query: str, **kwargs) -> str:
        """Generate response with conditional branching."""
        context = ChainContext(query=query, responses=[], metadata={})
        
        # Determine which branch to use
        selected_models = self._select_branch(query, context)
        
        # Process the selected branch
        for i, model in enumerate(selected_models):
            try:
                if isinstance(model, str):
                    model_name = model
                    logger.warning(f"String model '{model}' encountered, skipping")
                    continue
                else:
                    model_name = getattr(model, 'name', f'model_{i}')
                
                # Format prompt
                prompt = self._format_prompt(context, model_name, i, len(selected_models))
                
                # Generate response
                response = await model.generate(prompt, **kwargs)
                
                # Add to context
                context.add_response(response, model_name)
                
                # Check for mid-chain branching
                if i < len(selected_models) - 1:
                    new_branch = self._check_conditions(query, context)
                    if new_branch and new_branch in self.branches:
                        logger.info(f"Switching to branch '{new_branch}' at step {i+1}")
                        selected_models = self.branches[new_branch]
                        # Continue with the new branch from the next step
                        continue
                
            except Exception as e:
                logger.error(f"Error in conditional chain step {i+1}: {e}")
                
                if self.stop_on_error:
                    raise
                else:
                    error_response = f"[Error in {model_name}: {str(e)}]"
                    context.add_response(error_response, model_name)
        
        return context.responses[-1] if context.responses else ""
    
    def _select_branch(self, query: str, context: ChainContext) -> List[Union[Model, str]]:
        """Select which branch of models to use."""
        # Check conditions to determine branch
        selected_branch = self._check_conditions(query, context)
        
        if selected_branch and selected_branch in self.branches:
            logger.info(f"Selected branch: {selected_branch}")
            return self.branches[selected_branch]
        else:
            # Use default models
            return self.models
    
    def _check_conditions(self, query: str, context: ChainContext) -> Optional[str]:
        """Check all conditions and return the first matching branch."""
        for branch_name, condition_func in self.conditions.items():
            try:
                if condition_func(query, context):
                    return branch_name
            except Exception as e:
                logger.error(f"Error evaluating condition for branch '{branch_name}': {e}")
                continue
        
        return None


def create_chain(chain_type: str, **kwargs) -> Chain:
    """
    Factory function to create chains.
    
    Args:
        chain_type: Type of chain ("basic", "summarizing", "conditional")
        **kwargs: Chain-specific parameters
        
    Returns:
        Chain instance
    """
    chain_map = {
        "basic": Chain,
        "summarizing": SummarizingChain,
        "conditional": ConditionalChain,
    }
    
    if chain_type not in chain_map:
        raise ValueError(f"Unsupported chain type: {chain_type}")
    
    return chain_map[chain_type](**kwargs) 