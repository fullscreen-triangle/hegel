"""
Mixers for combining responses from multiple domain experts in Diadochi.

This module provides various strategies for combining and synthesizing responses
from multiple models into coherent, integrated responses.
"""

import logging
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from .models import Model

logger = logging.getLogger(__name__)


@dataclass
class WeightedResponse:
    """A response with associated weight/confidence."""
    content: str
    weight: float
    source: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Mixer(ABC):
    """Abstract base class for all mixers."""
    
    @abstractmethod
    async def mix(
        self, 
        query: str, 
        responses: Dict[str, str], 
        weights: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Mix multiple responses into a single response.
        
        Args:
            query: Original query
            responses: Dictionary mapping source names to responses
            weights: Optional weights for each response
            
        Returns:
            Mixed response
        """
        pass


class DefaultMixer(Mixer):
    """Returns the response with highest weight/confidence."""
    
    async def mix(
        self, 
        query: str, 
        responses: Dict[str, str], 
        weights: Optional[Dict[str, float]] = None
    ) -> str:
        """Return the highest weighted response."""
        if not responses:
            return ""
        
        if not weights:
            # Return the first response if no weights provided
            return next(iter(responses.values()))
        
        # Find the response with highest weight
        best_source = max(weights.keys(), key=lambda k: weights.get(k, 0.0))
        
        if best_source in responses:
            return responses[best_source]
        else:
            return next(iter(responses.values()))


class ConcatenationMixer(Mixer):
    """Concatenates responses with domain labels."""
    
    def __init__(self, include_weights: bool = True, separator: str = "\n\n"):
        """
        Initialize the concatenation mixer.
        
        Args:
            include_weights: Whether to include weights in output
            separator: Separator between responses
        """
        self.include_weights = include_weights
        self.separator = separator
    
    async def mix(
        self, 
        query: str, 
        responses: Dict[str, str], 
        weights: Optional[Dict[str, float]] = None
    ) -> str:
        """Concatenate responses with labels."""
        if not responses:
            return ""
        
        mixed_parts = []
        
        # Sort by weight if available
        if weights:
            sorted_sources = sorted(responses.keys(), key=lambda k: weights.get(k, 0.0), reverse=True)
        else:
            sorted_sources = list(responses.keys())
        
        for source in sorted_sources:
            response = responses[source]
            
            # Create header
            if self.include_weights and weights and source in weights:
                header = f"[{source} ({weights[source]:.1%})]:"
            else:
                header = f"[{source}]:"
            
            mixed_parts.append(f"{header}\n{response}")
        
        return self.separator.join(mixed_parts)


class SynthesisMixer(Mixer):
    """Uses an LLM to synthesize multiple responses."""
    
    def __init__(
        self, 
        synthesis_model: Model,
        prompt_template: Optional[str] = None,
        max_input_length: Optional[int] = None
    ):
        """
        Initialize the synthesis mixer.
        
        Args:
            synthesis_model: Model to use for synthesis
            prompt_template: Template for synthesis prompts
            max_input_length: Maximum input length for synthesis
        """
        self.synthesis_model = synthesis_model
        self.max_input_length = max_input_length
        self.prompt_template = prompt_template or self._default_prompt_template()
    
    def _default_prompt_template(self) -> str:
        """Default synthesis prompt template."""
        return """
You are tasked with synthesizing responses from multiple domain experts into a coherent, integrated response.

Original query: {query}

Expert responses:
{weighted_responses}

Create a unified response that:
1. Integrates insights from all relevant experts
2. Resolves any contradictions or conflicts
3. Provides a coherent narrative
4. Gives appropriate weight to each domain based on relevance
5. Directly addresses the original query

Synthesized response:
"""
    
    async def mix(
        self, 
        query: str, 
        responses: Dict[str, str], 
        weights: Optional[Dict[str, float]] = None
    ) -> str:
        """Synthesize responses using an LLM."""
        if not responses:
            return ""
        
        if len(responses) == 1:
            # No need to synthesize a single response
            return next(iter(responses.values()))
        
        try:
            # Format weighted responses
            weighted_responses = self._format_weighted_responses(responses, weights)
            
            # Truncate if needed
            if self.max_input_length:
                weighted_responses = self._truncate_responses(weighted_responses, self.max_input_length)
            
            # Create synthesis prompt
            prompt = self.prompt_template.format(
                query=query,
                weighted_responses=weighted_responses
            )
            
            # Generate synthesis
            synthesis = await self.synthesis_model.generate(prompt)
            
            return synthesis.strip()
            
        except Exception as e:
            logger.error(f"Error in synthesis mixing: {e}")
            # Fallback to concatenation
            fallback_mixer = ConcatenationMixer()
            return await fallback_mixer.mix(query, responses, weights)
    
    def _format_weighted_responses(
        self, 
        responses: Dict[str, str], 
        weights: Optional[Dict[str, float]]
    ) -> str:
        """Format responses with weights for synthesis."""
        formatted_parts = []
        
        # Sort by weight if available
        if weights:
            sorted_sources = sorted(responses.keys(), key=lambda k: weights.get(k, 0.0), reverse=True)
        else:
            sorted_sources = list(responses.keys())
        
        for source in sorted_sources:
            response = responses[source]
            
            if weights and source in weights:
                header = f"[{source} - Confidence: {weights[source]:.1%}]"
            else:
                header = f"[{source}]"
            
            formatted_parts.append(f"{header}\n{response}")
        
        return "\n\n".join(formatted_parts)
    
    def _truncate_responses(self, formatted_responses: str, max_length: int) -> str:
        """Truncate responses if they exceed maximum length."""
        if len(formatted_responses) <= max_length:
            return formatted_responses
        
        logger.warning(f"Truncating responses from {len(formatted_responses)} to {max_length} characters")
        
        # Simple truncation with ellipsis
        return formatted_responses[:max_length-10] + "\n\n[...]"


class WeightedMixer(Mixer):
    """Combines responses based on confidence scores using weighted averaging techniques."""
    
    def __init__(
        self, 
        combination_method: str = "weighted_segments",
        segment_length: int = 100,
        overlap_penalty: float = 0.1
    ):
        """
        Initialize the weighted mixer.
        
        Args:
            combination_method: Method for combining ("weighted_segments", "sentence_selection", "paragraph_blend")
            segment_length: Length of segments for weighted combination
            overlap_penalty: Penalty for overlapping content
        """
        self.combination_method = combination_method
        self.segment_length = segment_length
        self.overlap_penalty = overlap_penalty
    
    async def mix(
        self, 
        query: str, 
        responses: Dict[str, str], 
        weights: Optional[Dict[str, float]] = None
    ) -> str:
        """Combine responses using weighted techniques."""
        if not responses:
            return ""
        
        if len(responses) == 1:
            return next(iter(responses.values()))
        
        if not weights:
            # Equal weights if none provided
            weights = {source: 1.0/len(responses) for source in responses.keys()}
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}
        
        # Apply combination method
        if self.combination_method == "weighted_segments":
            return await self._weighted_segments_combination(responses, weights)
        elif self.combination_method == "sentence_selection":
            return await self._sentence_selection_combination(responses, weights)
        elif self.combination_method == "paragraph_blend":
            return await self._paragraph_blend_combination(responses, weights)
        else:
            raise ValueError(f"Unknown combination method: {self.combination_method}")
    
    async def _weighted_segments_combination(
        self, 
        responses: Dict[str, str], 
        weights: Dict[str, float]
    ) -> str:
        """Combine responses by selecting segments based on weights."""
        # Create weighted response list
        weighted_responses = []
        for source, response in responses.items():
            weight = weights.get(source, 0.0)
            weighted_responses.append(WeightedResponse(response, weight, source))
        
        # Sort by weight
        weighted_responses.sort(key=lambda x: x.weight, reverse=True)
        
        # Combine segments
        combined_segments = []
        used_content = set()
        
        for wr in weighted_responses:
            segments = self._split_into_segments(wr.content, self.segment_length)
            
            for segment in segments:
                # Check for overlap with already used content
                if not self._has_significant_overlap(segment, used_content):
                    combined_segments.append((segment, wr.weight, wr.source))
                    used_content.add(segment.lower().strip())
        
        # Sort segments by weight and combine
        combined_segments.sort(key=lambda x: x[1], reverse=True)
        
        # Take the best segments up to a reasonable length
        final_segments = []
        total_length = 0
        max_length = max(len(response) for response in responses.values()) * 1.2
        
        for segment, weight, source in combined_segments:
            if total_length + len(segment) <= max_length:
                final_segments.append(segment)
                total_length += len(segment)
            else:
                break
        
        return " ".join(final_segments)
    
    async def _sentence_selection_combination(
        self, 
        responses: Dict[str, str], 
        weights: Dict[str, float]
    ) -> str:
        """Combine responses by selecting sentences based on weights."""
        # Extract sentences from all responses
        weighted_sentences = []
        
        for source, response in responses.items():
            weight = weights.get(source, 0.0)
            sentences = self._split_into_sentences(response)
            
            for sentence in sentences:
                weighted_sentences.append((sentence, weight, source))
        
        # Sort by weight and remove duplicates
        weighted_sentences.sort(key=lambda x: x[1], reverse=True)
        
        used_sentences = set()
        final_sentences = []
        
        for sentence, weight, source in weighted_sentences:
            # Check for near-duplicates
            sentence_lower = sentence.lower().strip()
            if not any(self._sentences_similar(sentence_lower, used) for used in used_sentences):
                final_sentences.append(sentence)
                used_sentences.add(sentence_lower)
        
        return " ".join(final_sentences)
    
    async def _paragraph_blend_combination(
        self, 
        responses: Dict[str, str], 
        weights: Dict[str, float]
    ) -> str:
        """Combine responses by blending paragraphs based on weights."""
        # Split responses into paragraphs
        paragraph_groups = []
        
        for source, response in responses.items():
            weight = weights.get(source, 0.0)
            paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
            
            for i, paragraph in enumerate(paragraphs):
                # Group paragraphs by topic similarity (simplified)
                topic_group = i % 3  # Simple grouping
                paragraph_groups.append((paragraph, weight, source, topic_group))
        
        # Group by topic and select best from each group
        topic_paragraphs = {}
        for paragraph, weight, source, topic in paragraph_groups:
            if topic not in topic_paragraphs:
                topic_paragraphs[topic] = []
            topic_paragraphs[topic].append((paragraph, weight, source))
        
        # Select best paragraph from each topic group
        final_paragraphs = []
        for topic, paragraphs in topic_paragraphs.items():
            # Sort by weight and take the best
            paragraphs.sort(key=lambda x: x[1], reverse=True)
            if paragraphs:
                final_paragraphs.append(paragraphs[0][0])
        
        return "\n\n".join(final_paragraphs)
    
    def _split_into_segments(self, text: str, segment_length: int) -> List[str]:
        """Split text into segments of approximately equal length."""
        words = text.split()
        segments = []
        
        current_segment = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= segment_length:
                current_segment.append(word)
                current_length += len(word) + 1
            else:
                if current_segment:
                    segments.append(" ".join(current_segment))
                current_segment = [word]
                current_length = len(word)
        
        if current_segment:
            segments.append(" ".join(current_segment))
        
        return segments
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences (simple implementation)."""
        import re
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _has_significant_overlap(self, segment: str, used_content: set) -> bool:
        """Check if segment has significant overlap with used content."""
        segment_lower = segment.lower().strip()
        
        for used in used_content:
            if len(segment_lower) > 0 and len(used) > 0:
                # Calculate Jaccard similarity
                seg_words = set(segment_lower.split())
                used_words = set(used.split())
                
                if seg_words and used_words:
                    intersection = len(seg_words.intersection(used_words))
                    union = len(seg_words.union(used_words))
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity > self.overlap_penalty:
                        return True
        
        return False
    
    def _sentences_similar(self, sent1: str, sent2: str, threshold: float = 0.7) -> bool:
        """Check if two sentences are similar."""
        if not sent1 or not sent2:
            return False
        
        words1 = set(sent1.split())
        words2 = set(sent2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold


class ConsensusBasedMixer(Mixer):
    """Finds consensus among responses and builds a unified answer."""
    
    def __init__(
        self, 
        consensus_threshold: float = 0.6,
        conflict_resolution: str = "weight_based"
    ):
        """
        Initialize the consensus-based mixer.
        
        Args:
            consensus_threshold: Minimum agreement threshold for consensus
            conflict_resolution: How to resolve conflicts ("weight_based", "majority", "expert_priority")
        """
        self.consensus_threshold = consensus_threshold
        self.conflict_resolution = conflict_resolution
    
    async def mix(
        self, 
        query: str, 
        responses: Dict[str, str], 
        weights: Optional[Dict[str, float]] = None
    ) -> str:
        """Find consensus among responses."""
        if not responses:
            return ""
        
        if len(responses) == 1:
            return next(iter(responses.values()))
        
        # Extract key points from each response
        key_points = {}
        for source, response in responses.items():
            points = self._extract_key_points(response)
            key_points[source] = points
        
        # Find consensus points
        consensus_points = self._find_consensus(key_points, weights or {})
        
        # Handle conflicts
        conflict_resolutions = self._resolve_conflicts(key_points, weights or {})
        
        # Build unified response
        unified_response = self._build_unified_response(
            consensus_points, 
            conflict_resolutions, 
            query
        )
        
        return unified_response
    
    def _extract_key_points(self, response: str) -> List[str]:
        """Extract key points from a response (simplified implementation)."""
        # Split into sentences and filter for key points
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        
        # Simple heuristic: longer sentences are more likely to be key points
        key_points = [s for s in sentences if len(s) > 20]
        
        return key_points[:5]  # Limit to top 5 key points
    
    def _find_consensus(
        self, 
        key_points: Dict[str, List[str]], 
        weights: Dict[str, float]
    ) -> List[str]:
        """Find points that have consensus across responses."""
        consensus_points = []
        
        # Compare all pairs of key points
        all_points = []
        for source, points in key_points.items():
            weight = weights.get(source, 1.0)
            all_points.extend([(point, source, weight) for point in points])
        
        # Group similar points
        point_groups = []
        used_points = set()
        
        for i, (point1, source1, weight1) in enumerate(all_points):
            if i in used_points:
                continue
            
            group = [(point1, source1, weight1)]
            used_points.add(i)
            
            for j, (point2, source2, weight2) in enumerate(all_points[i+1:], i+1):
                if j in used_points:
                    continue
                
                if self._points_similar(point1, point2):
                    group.append((point2, source2, weight2))
                    used_points.add(j)
            
            if len(group) >= len(key_points) * self.consensus_threshold:
                # This is a consensus point
                best_point = max(group, key=lambda x: x[2])[0]  # Select highest weighted version
                consensus_points.append(best_point)
        
        return consensus_points
    
    def _resolve_conflicts(
        self, 
        key_points: Dict[str, List[str]], 
        weights: Dict[str, float]
    ) -> List[str]:
        """Resolve conflicts between responses."""
        # Simplified conflict resolution
        if self.conflict_resolution == "weight_based":
            # Select points from highest weighted sources
            sorted_sources = sorted(weights.items(), key=lambda x: x[1], reverse=True)
            
            conflict_resolutions = []
            for source, weight in sorted_sources[:2]:  # Take top 2 sources
                if source in key_points:
                    conflict_resolutions.extend(key_points[source][:2])  # Top 2 points each
            
            return conflict_resolutions
        
        return []
    
    def _build_unified_response(
        self, 
        consensus_points: List[str], 
        conflict_resolutions: List[str], 
        query: str
    ) -> str:
        """Build a unified response from consensus and conflict resolution."""
        response_parts = []
        
        if consensus_points:
            response_parts.append("Based on expert consensus:")
            for point in consensus_points:
                response_parts.append(f"• {point}")
        
        if conflict_resolutions:
            if response_parts:
                response_parts.append("\nAdditional considerations:")
            else:
                response_parts.append("Key insights:")
            
            for resolution in conflict_resolutions:
                response_parts.append(f"• {resolution}")
        
        return "\n".join(response_parts) if response_parts else "No clear consensus found among expert responses."
    
    def _points_similar(self, point1: str, point2: str, threshold: float = 0.5) -> bool:
        """Check if two points are similar."""
        if not point1 or not point2:
            return False
        
        words1 = set(point1.lower().split())
        words2 = set(point2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold


def create_mixer(mixer_type: str, **kwargs) -> Mixer:
    """
    Factory function to create mixers.
    
    Args:
        mixer_type: Type of mixer ("default", "concatenation", "synthesis", "weighted", "consensus")
        **kwargs: Mixer-specific parameters
        
    Returns:
        Mixer instance
    """
    mixer_map = {
        "default": DefaultMixer,
        "concatenation": ConcatenationMixer,
        "synthesis": SynthesisMixer,
        "weighted": WeightedMixer,
        "consensus": ConsensusBasedMixer,
    }
    
    if mixer_type not in mixer_map:
        raise ValueError(f"Unsupported mixer type: {mixer_type}")
    
    return mixer_map[mixer_type](**kwargs) 