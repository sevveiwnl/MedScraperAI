"""Summarizer service for generating article summaries."""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from openai import OpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings


logger = logging.getLogger(__name__)


class SummarizerType(str, Enum):
    """Available summarizer types."""

    OPENAI = "openai"
    BART = "bart"  # Will be implemented later


class SummarizerService:
    """Service for generating article summaries using various AI models."""

    def __init__(self, summarizer_type: SummarizerType = SummarizerType.OPENAI):
        """
        Initialize the summarizer service.

        Args:
            summarizer_type: Type of summarizer to use
        """
        self.summarizer_type = summarizer_type
        self.client = None

        if summarizer_type == SummarizerType.OPENAI:
            self._init_openai_client()

    def _init_openai_client(self):
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            return

        try:
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def _summarize_text_with_retry(
        self,
        text: str,
        max_length: int = 200,
        min_length: int = 50,
        style: str = "professional",
        focus: str = "medical",
    ) -> Dict[str, Any]:
        """
        Internal method to generate a summary with retry logic.
        """
        if self.summarizer_type == SummarizerType.OPENAI:
            return self._summarize_with_openai(
                text, max_length, min_length, style, focus
            )
        elif self.summarizer_type == SummarizerType.BART:
            return self._summarize_with_bart(text, max_length, min_length, style, focus)
        else:
            return {
                "success": False,
                "error": f"Unsupported summarizer type: {self.summarizer_type}",
                "summary": None,
                "metadata": {
                    "summarizer_type": self.summarizer_type.value,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

    def summarize_text(
        self,
        text: str,
        max_length: int = 200,
        min_length: int = 50,
        style: str = "professional",
        focus: str = "medical",
    ) -> Dict[str, Any]:
        """
        Generate a summary of the given text.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary in words
            min_length: Minimum length of summary in words
            style: Style of summary (professional, casual, academic)
            focus: Focus area for summary (medical, general, technical)

        Returns:
            Dictionary containing summary and metadata
        """
        if not text or len(text.strip()) < 100:
            return {
                "success": False,
                "error": "Text is too short to summarize (minimum 100 characters)",
                "summary": None,
                "metadata": {
                    "original_length": len(text),
                    "summarizer_type": self.summarizer_type.value,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        try:
            return self._summarize_text_with_retry(
                text, max_length, min_length, style, focus
            )
        except Exception as e:
            logger.error(f"Summarization failed after retries: {str(e)}")
            return {
                "success": False,
                "error": f"Summarization failed after retries: {str(e)}",
                "summary": None,
                "metadata": {
                    "summarizer_type": self.summarizer_type.value,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

    def _summarize_with_openai(
        self,
        text: str,
        max_length: int,
        min_length: int,
        style: str,
        focus: str,
    ) -> Dict[str, Any]:
        """
        Generate summary using OpenAI GPT models.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            min_length: Minimum length of summary
            style: Style of summary
            focus: Focus area for summary

        Returns:
            Dictionary containing summary and metadata
        """
        if not self.client:
            return {
                "success": False,
                "error": "OpenAI client not initialized. Please check OPENAI_API_KEY.",
                "summary": None,
                "metadata": {
                    "summarizer_type": self.summarizer_type.value,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        try:
            # Prepare the prompt based on focus and style
            system_prompt = self._create_system_prompt(
                style, focus, max_length, min_length
            )

            # Truncate text if too long (OpenAI has token limits)
            max_input_chars = 12000  # Conservative limit to avoid token issues
            if len(text) > max_input_chars:
                text = text[:max_input_chars] + "..."
                logger.warning(f"Text truncated to {max_input_chars} characters")

            # Make API call
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Please summarize the following text:\n\n{text}",
                    },
                ],
                max_tokens=int(
                    max_length * 1.5
                ),  # Rough conversion from words to tokens
                temperature=0.3,
                top_p=0.9,
                frequency_penalty=0.0,
                presence_penalty=0.0,
            )

            summary = response.choices[0].message.content.strip()

            # Validate summary length
            summary_words = len(summary.split())
            if summary_words < min_length:
                logger.warning(
                    f"Summary too short: {summary_words} words (minimum: {min_length})"
                )
            elif summary_words > max_length:
                logger.warning(
                    f"Summary too long: {summary_words} words (maximum: {max_length})"
                )

            return {
                "success": True,
                "summary": summary,
                "metadata": {
                    "summarizer_type": self.summarizer_type.value,
                    "model": "gpt-3.5-turbo",
                    "original_length": len(text),
                    "summary_length": len(summary),
                    "summary_words": summary_words,
                    "compression_ratio": len(summary) / len(text) if text else 0,
                    "style": style,
                    "focus": focus,
                    "timestamp": datetime.utcnow().isoformat(),
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    },
                },
            }

        except Exception as e:
            logger.error(f"OpenAI summarization failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "summary": None,
                "metadata": {
                    "summarizer_type": self.summarizer_type.value,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

    def _summarize_with_bart(
        self,
        text: str,
        max_length: int,
        min_length: int,
        style: str,
        focus: str,
    ) -> Dict[str, Any]:
        """
        Generate summary using BART model.

        This will be implemented in October 2024.
        """
        return {
            "success": False,
            "error": "BART summarizer will be implemented in October 2024",
            "summary": None,
            "metadata": {
                "summarizer_type": self.summarizer_type.value,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

    def _create_system_prompt(
        self, style: str, focus: str, max_length: int, min_length: int
    ) -> str:
        """
        Create system prompt for OpenAI based on parameters.

        Args:
            style: Style of summary
            focus: Focus area for summary
            max_length: Maximum length in words
            min_length: Minimum length in words

        Returns:
            System prompt string
        """
        style_instructions = {
            "professional": "Write in a professional, formal tone suitable for healthcare professionals and researchers.",
            "casual": "Write in a conversational, accessible tone suitable for general audiences.",
            "academic": "Write in an academic, scholarly tone with precise terminology.",
        }

        focus_instructions = {
            "medical": "Focus on medical findings, health implications, treatment options, and clinical significance.",
            "general": "Provide a balanced overview covering all key points and main takeaways.",
            "technical": "Emphasize technical details, methodology, and scientific aspects.",
        }

        return f"""You are an expert medical content summarizer. Your task is to create concise, accurate summaries of medical articles and research.

STYLE: {style_instructions.get(style, style_instructions["professional"])}

FOCUS: {focus_instructions.get(focus, focus_instructions["medical"])}

REQUIREMENTS:
- Length: {min_length}-{max_length} words
- Preserve key medical facts, statistics, and findings
- Maintain accuracy and avoid speculation
- Use clear, precise language
- Include the most important information first
- Avoid unnecessary jargon while maintaining precision
- Do not include personal opinions or interpretations

Please provide only the summary without any additional commentary."""

    def summarize_article(
        self,
        title: str,
        content: str,
        author: Optional[str] = None,
        source: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a summary specifically for article content.

        Args:
            title: Article title
            content: Article content
            author: Article author (optional)
            source: Article source (optional)
            **kwargs: Additional arguments for summarization

        Returns:
            Dictionary containing summary and metadata
        """
        # Combine title and content for better context
        full_text = f"Title: {title}\n\n{content}"

        # Add source information if available
        if author:
            full_text = f"Author: {author}\n{full_text}"
        if source:
            full_text = f"Source: {source}\n{full_text}"

        # Set defaults for article summarization
        kwargs.setdefault("max_length", 150)
        kwargs.setdefault("min_length", 50)
        kwargs.setdefault("style", "professional")
        kwargs.setdefault("focus", "medical")

        result = self.summarize_text(full_text, **kwargs)

        # Add article-specific metadata
        if result["success"]:
            result["metadata"].update(
                {
                    "title": title,
                    "author": author,
                    "source": source,
                    "content_length": len(content),
                }
            )

        return result

    def batch_summarize(self, texts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        Generate summaries for multiple texts.

        Args:
            texts: List of texts to summarize
            **kwargs: Additional arguments for summarization

        Returns:
            List of dictionaries containing summaries and metadata
        """
        results = []

        for i, text in enumerate(texts):
            try:
                logger.info(f"Summarizing text {i+1}/{len(texts)}")
                result = self.summarize_text(text, **kwargs)
                results.append(result)

                # Add batch metadata
                if result["success"]:
                    result["metadata"]["batch_index"] = i
                    result["metadata"]["batch_total"] = len(texts)

            except Exception as e:
                logger.error(f"Error summarizing text {i+1}: {str(e)}")
                results.append(
                    {
                        "success": False,
                        "error": str(e),
                        "summary": None,
                        "metadata": {
                            "batch_index": i,
                            "batch_total": len(texts),
                            "summarizer_type": self.summarizer_type.value,
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    }
                )

        return results

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the summarizer service.

        Returns:
            Dictionary containing service information
        """
        return {
            "summarizer_type": self.summarizer_type.value,
            "available_types": [t.value for t in SummarizerType],
            "openai_available": self.client is not None,
            "bart_available": False,  # Will be True in October 2024
            "service_name": "MedScraperAI Summarizer Service",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
