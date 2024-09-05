"""Tests for summarizer service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.summarizer_service import SummarizerService, SummarizerType


class TestSummarizerService:
    """Test summarizer service."""

    def test_init_openai_summarizer(self):
        """Test initializing OpenAI summarizer."""
        with patch("app.services.summarizer_service.OpenAI") as mock_openai:
            mock_openai.return_value = Mock()

            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                service = SummarizerService(SummarizerType.OPENAI)

                assert service.summarizer_type == SummarizerType.OPENAI
                assert service.client is not None
                mock_openai.assert_called_once_with(api_key="test-key")

    def test_init_openai_no_api_key(self):
        """Test initializing OpenAI summarizer without API key."""
        with patch.dict("os.environ", {}, clear=True):
            service = SummarizerService(SummarizerType.OPENAI)

            assert service.summarizer_type == SummarizerType.OPENAI
            assert service.client is None

    def test_init_bart_summarizer(self):
        """Test initializing BART summarizer."""
        service = SummarizerService(SummarizerType.BART)

        assert service.summarizer_type == SummarizerType.BART
        assert service.client is None

    def test_summarize_text_too_short(self):
        """Test summarizing text that is too short."""
        service = SummarizerService(SummarizerType.OPENAI)

        result = service.summarize_text("Short text")

        assert result["success"] is False
        assert "too short" in result["error"]
        assert result["summary"] is None

    @patch("app.services.summarizer_service.OpenAI")
    def test_summarize_text_openai_success(self, mock_openai):
        """Test successful OpenAI text summarization."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "This is a test summary of the medical article."
        )
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = SummarizerService(SummarizerType.OPENAI)

            text = (
                "This is a long medical article about heart disease and cardiovascular health. "
                * 10
            )
            result = service.summarize_text(text)

            assert result["success"] is True
            assert result["summary"] == "This is a test summary of the medical article."
            assert result["metadata"]["summarizer_type"] == "openai"
            assert result["metadata"]["model"] == "gpt-3.5-turbo"
            assert result["metadata"]["usage"]["total_tokens"] == 150

            # Verify OpenAI API was called correctly
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["model"] == "gpt-3.5-turbo"
            assert call_args[1]["temperature"] == 0.3

    @patch("app.services.summarizer_service.OpenAI")
    def test_summarize_text_openai_failure(self, mock_openai):
        """Test OpenAI text summarization failure."""
        # Mock OpenAI client to raise exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = SummarizerService(SummarizerType.OPENAI)

            text = (
                "This is a long medical article about heart disease and cardiovascular health. "
                * 10
            )
            result = service.summarize_text(text)

            assert result["success"] is False
            assert "API Error" in result["error"]
            assert result["summary"] is None

    def test_summarize_text_no_client(self):
        """Test summarizing text without initialized client."""
        service = SummarizerService(SummarizerType.OPENAI)
        service.client = None

        text = (
            "This is a long medical article about heart disease and cardiovascular health. "
            * 10
        )
        result = service.summarize_text(text)

        assert result["success"] is False
        assert "not initialized" in result["error"]
        assert result["summary"] is None

    def test_summarize_text_bart_not_implemented(self):
        """Test BART summarization (not implemented yet)."""
        service = SummarizerService(SummarizerType.BART)

        text = (
            "This is a long medical article about heart disease and cardiovascular health. "
            * 10
        )
        result = service.summarize_text(text)

        assert result["success"] is False
        assert "October 2024" in result["error"]
        assert result["summary"] is None

    def test_create_system_prompt_professional_medical(self):
        """Test creating system prompt for professional medical style."""
        service = SummarizerService(SummarizerType.OPENAI)

        prompt = service._create_system_prompt("professional", "medical", 150, 50)

        assert "professional" in prompt
        assert "medical" in prompt
        assert "50-150 words" in prompt
        assert "healthcare professionals" in prompt

    def test_create_system_prompt_casual_general(self):
        """Test creating system prompt for casual general style."""
        service = SummarizerService(SummarizerType.OPENAI)

        prompt = service._create_system_prompt("casual", "general", 200, 100)

        assert "conversational" in prompt
        assert "general" in prompt
        assert "100-200 words" in prompt

    @patch("app.services.summarizer_service.OpenAI")
    def test_summarize_article_success(self, mock_openai):
        """Test successful article summarization."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "This is a summary of the medical article."
        )
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = SummarizerService(SummarizerType.OPENAI)

            result = service.summarize_article(
                title="Heart Disease Research",
                content="This is a comprehensive article about heart disease and cardiovascular health. "
                * 20,
                author="Dr. Smith",
                source="Medical Journal",
            )

            assert result["success"] is True
            assert result["summary"] == "This is a summary of the medical article."
            assert result["metadata"]["title"] == "Heart Disease Research"
            assert result["metadata"]["author"] == "Dr. Smith"
            assert result["metadata"]["source"] == "Medical Journal"

    @patch("app.services.summarizer_service.OpenAI")
    def test_batch_summarize_success(self, mock_openai):
        """Test successful batch summarization."""
        # Mock OpenAI client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test summary."
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = SummarizerService(SummarizerType.OPENAI)

            texts = [
                "This is a long medical article about heart disease. " * 10,
                "This is another article about diabetes treatment. " * 10,
            ]

            results = service.batch_summarize(texts)

            assert len(results) == 2
            assert all(r["success"] for r in results)
            assert all(r["summary"] == "This is a test summary." for r in results)
            assert results[0]["metadata"]["batch_index"] == 0
            assert results[1]["metadata"]["batch_index"] == 1

    @patch("app.services.summarizer_service.OpenAI")
    def test_batch_summarize_partial_failure(self, mock_openai):
        """Test batch summarization with partial failures."""
        # Mock OpenAI client with alternating success/failure
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test summary."
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150

        # First call succeeds, second fails
        mock_client.chat.completions.create.side_effect = [
            mock_response,
            Exception("API Error"),
        ]
        mock_openai.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            service = SummarizerService(SummarizerType.OPENAI)

            texts = [
                "This is a long medical article about heart disease. " * 10,
                "This is another article about diabetes treatment. " * 10,
            ]

            results = service.batch_summarize(texts)

            assert len(results) == 2
            assert results[0]["success"] is True
            assert results[1]["success"] is False
            assert "API Error" in results[1]["error"]

    def test_get_service_info_openai(self):
        """Test getting service info for OpenAI summarizer."""
        with patch("app.services.summarizer_service.OpenAI") as mock_openai:
            mock_openai.return_value = Mock()

            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                service = SummarizerService(SummarizerType.OPENAI)

                info = service.get_service_info()

                assert info["summarizer_type"] == "openai"
                assert info["openai_available"] is True
                assert info["bart_available"] is False
                assert "openai" in info["available_types"]
                assert "bart" in info["available_types"]

    def test_get_service_info_no_openai(self):
        """Test getting service info without OpenAI."""
        with patch.dict("os.environ", {}, clear=True):
            service = SummarizerService(SummarizerType.OPENAI)

            info = service.get_service_info()

            assert info["summarizer_type"] == "openai"
            assert info["openai_available"] is False
            assert info["bart_available"] is False

    def test_summarize_text_with_custom_parameters(self):
        """Test text summarization with custom parameters."""
        with patch("app.services.summarizer_service.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Custom summary."
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150

            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                service = SummarizerService(SummarizerType.OPENAI)

                text = "This is a long medical article about heart disease. " * 10
                result = service.summarize_text(
                    text=text,
                    max_length=300,
                    min_length=100,
                    style="academic",
                    focus="technical",
                )

                assert result["success"] is True
                assert result["metadata"]["style"] == "academic"
                assert result["metadata"]["focus"] == "technical"

                # Verify the system prompt was created with correct parameters
                call_args = mock_client.chat.completions.create.call_args
                system_message = call_args[1]["messages"][0]["content"]
                assert "100-300 words" in system_message
                assert "academic" in system_message
                assert "technical" in system_message

    def test_summarize_text_truncation(self):
        """Test text truncation for long inputs."""
        with patch("app.services.summarizer_service.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Truncated summary."
            mock_response.usage.prompt_tokens = 100
            mock_response.usage.completion_tokens = 50
            mock_response.usage.total_tokens = 150

            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
                service = SummarizerService(SummarizerType.OPENAI)

                # Create very long text
                long_text = "This is a very long medical article. " * 1000
                result = service.summarize_text(long_text)

                assert result["success"] is True

                # Verify text was truncated
                call_args = mock_client.chat.completions.create.call_args
                user_message = call_args[1]["messages"][1]["content"]
                assert "..." in user_message  # Truncation indicator

    def test_unsupported_summarizer_type(self):
        """Test using unsupported summarizer type."""
        service = SummarizerService(SummarizerType.OPENAI)
        service.summarizer_type = "unsupported"

        text = "This is a long medical article about heart disease. " * 10
        result = service.summarize_text(text)

        assert result["success"] is False
        assert "Unsupported summarizer type" in result["error"]
        assert result["summary"] is None
