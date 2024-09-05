"""Tests for article endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.article import Article
from app.db.session import get_db


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_db(client):
    """Get test database session."""

    def override_get_db():
        # This would normally be a test database session
        # For now, we'll use the default one
        yield from get_db()

    app.dependency_overrides[get_db] = override_get_db
    yield override_get_db
    app.dependency_overrides = {}


@pytest.fixture
def sample_article_data():
    """Create sample article data for testing."""
    return {
        "title": "Test Medical Article",
        "content": "This is a test medical article with detailed content about health research.",
        "source": "Test Medical Journal",
        "url": "https://example.com/test-article",
        "author": "Dr. Test Author",
        "published_at": "2024-09-05T10:00:00Z",
        "category": "Research",
        "tags": "health, research, medical",
        "summary": "A test article about medical research.",
        "credibility_score": 0.9,
    }


class TestArticleEndpoints:
    """Test article endpoints."""

    def test_create_article_success(self, client, sample_article_data):
        """Test successful article creation."""
        response = client.post("/api/v1/articles/", json=sample_article_data)

        assert response.status_code == 201
        data = response.json()

        assert data["title"] == sample_article_data["title"]
        assert data["content"] == sample_article_data["content"]
        assert data["source"] == sample_article_data["source"]
        assert data["url"] == sample_article_data["url"]
        assert data["author"] == sample_article_data["author"]
        assert data["category"] == sample_article_data["category"]
        assert data["credibility_score"] == sample_article_data["credibility_score"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_article_invalid_data(self, client):
        """Test article creation with invalid data."""
        invalid_data = {
            "title": "",  # Empty title
            "content": "Test content",
            "source": "Test Source",
            "url": "invalid-url",  # Invalid URL
        }

        response = client.post("/api/v1/articles/", json=invalid_data)
        assert response.status_code == 422

    def test_create_duplicate_article(self, client, sample_article_data):
        """Test creating duplicate article by URL."""
        # Create first article
        response1 = client.post("/api/v1/articles/", json=sample_article_data)
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post("/api/v1/articles/", json=sample_article_data)
        assert response2.status_code == 400
        assert "already exist" in response2.json()["detail"]

    def test_get_article_success(self, client, sample_article_data):
        """Test successful article retrieval."""
        # Create article first
        create_response = client.post("/api/v1/articles/", json=sample_article_data)
        article_id = create_response.json()["id"]

        # Get article
        response = client.get(f"/api/v1/articles/{article_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == article_id
        assert data["title"] == sample_article_data["title"]

    def test_get_article_not_found(self, client):
        """Test getting non-existent article."""
        response = client.get("/api/v1/articles/99999")
        assert response.status_code == 404

    def test_get_articles_list(self, client, sample_article_data):
        """Test getting articles list."""
        # Create a few articles
        for i in range(3):
            article_data = sample_article_data.copy()
            article_data["title"] = f"Test Article {i}"
            article_data["url"] = f"https://example.com/test-{i}"
            client.post("/api/v1/articles/", json=article_data)

        # Get articles list
        response = client.get("/api/v1/articles/")
        assert response.status_code == 200

        data = response.json()
        assert "articles" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "has_next" in data
        assert "has_prev" in data
        assert len(data["articles"]) >= 3

    def test_get_articles_with_filters(self, client, sample_article_data):
        """Test getting articles with filters."""
        # Create articles with different sources
        article1 = sample_article_data.copy()
        article1["source"] = "Source A"
        article1["url"] = "https://example.com/article-1"
        client.post("/api/v1/articles/", json=article1)

        article2 = sample_article_data.copy()
        article2["source"] = "Source B"
        article2["url"] = "https://example.com/article-2"
        client.post("/api/v1/articles/", json=article2)

        # Filter by source
        response = client.get("/api/v1/articles/?source=Source A")
        assert response.status_code == 200

        data = response.json()
        assert len(data["articles"]) >= 1
        for article in data["articles"]:
            assert "Source A" in article["source"]

    def test_get_articles_pagination(self, client, sample_article_data):
        """Test articles pagination."""
        # Create multiple articles
        for i in range(5):
            article_data = sample_article_data.copy()
            article_data["title"] = f"Test Article {i}"
            article_data["url"] = f"https://example.com/test-{i}"
            client.post("/api/v1/articles/", json=article_data)

        # Get first page
        response = client.get("/api/v1/articles/?limit=2&skip=0")
        assert response.status_code == 200

        data = response.json()
        assert len(data["articles"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is False

    def test_search_articles(self, client, sample_article_data):
        """Test article search functionality."""
        # Create articles with different content
        article1 = sample_article_data.copy()
        article1["title"] = "Heart Disease Research"
        article1["content"] = "This article discusses cardiovascular health"
        article1["url"] = "https://example.com/heart-disease"
        client.post("/api/v1/articles/", json=article1)

        article2 = sample_article_data.copy()
        article2["title"] = "Diabetes Treatment"
        article2["content"] = "This article covers diabetes management"
        article2["url"] = "https://example.com/diabetes"
        client.post("/api/v1/articles/", json=article2)

        # Search for heart-related articles
        response = client.get("/api/v1/articles/search/?q=heart")
        assert response.status_code == 200

        data = response.json()
        assert "articles" in data
        assert "query" in data
        assert "search_fields" in data
        assert data["query"] == "heart"
        assert len(data["articles"]) >= 1

    def test_update_article(self, client, sample_article_data):
        """Test article update."""
        # Create article
        create_response = client.post("/api/v1/articles/", json=sample_article_data)
        article_id = create_response.json()["id"]

        # Update article
        update_data = {"title": "Updated Title", "credibility_score": 0.95}

        response = client.put(f"/api/v1/articles/{article_id}", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["credibility_score"] == 0.95

    def test_update_article_not_found(self, client):
        """Test updating non-existent article."""
        update_data = {"title": "Updated Title"}
        response = client.put("/api/v1/articles/99999", json=update_data)
        assert response.status_code == 404

    def test_delete_article(self, client, sample_article_data):
        """Test article deletion."""
        # Create article
        create_response = client.post("/api/v1/articles/", json=sample_article_data)
        article_id = create_response.json()["id"]

        # Delete article
        response = client.delete(f"/api/v1/articles/{article_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/articles/{article_id}")
        assert get_response.status_code == 404

    def test_delete_article_not_found(self, client):
        """Test deleting non-existent article."""
        response = client.delete("/api/v1/articles/99999")
        assert response.status_code == 404

    def test_bulk_create_articles(self, client, sample_article_data):
        """Test bulk article creation."""
        articles_data = []
        for i in range(3):
            article_data = sample_article_data.copy()
            article_data["title"] = f"Bulk Article {i}"
            article_data["url"] = f"https://example.com/bulk-{i}"
            articles_data.append(article_data)

        response = client.post("/api/v1/articles/bulk", json=articles_data)
        assert response.status_code == 200

        data = response.json()
        assert data["created_count"] == 3
        assert data["total_count"] == 3
        assert len(data["articles"]) == 3
        assert len(data["errors"]) == 0

    def test_get_article_statistics(self, client, sample_article_data):
        """Test getting article statistics."""
        # Create a few articles
        for i in range(3):
            article_data = sample_article_data.copy()
            article_data["title"] = f"Stats Article {i}"
            article_data["url"] = f"https://example.com/stats-{i}"
            client.post("/api/v1/articles/", json=article_data)

        response = client.get("/api/v1/articles/stats/summary")
        assert response.status_code == 200

        data = response.json()
        assert "total_articles" in data
        assert "recent_articles" in data
        assert "average_credibility" in data
        assert "high_credibility_articles" in data
        assert "sources" in data
        assert "categories" in data
        assert "last_updated" in data

    def test_get_similar_articles(self, client, sample_article_data):
        """Test getting similar articles."""
        # Create base article
        create_response = client.post("/api/v1/articles/", json=sample_article_data)
        article_id = create_response.json()["id"]

        # Create similar article
        similar_data = sample_article_data.copy()
        similar_data["title"] = "Similar Medical Article"
        similar_data["url"] = "https://example.com/similar"
        client.post("/api/v1/articles/", json=similar_data)

        # Get similar articles
        response = client.get(f"/api/v1/articles/{article_id}/similar")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_get_similar_articles_not_found(self, client):
        """Test getting similar articles for non-existent article."""
        response = client.get("/api/v1/articles/99999/similar")
        assert response.status_code == 404

    def test_get_article_by_url(self, client, sample_article_data):
        """Test getting article by URL."""
        # Create article
        create_response = client.post("/api/v1/articles/", json=sample_article_data)

        # Get article by URL
        response = client.get(
            f"/api/v1/articles/by-url/?url={sample_article_data['url']}"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["url"] == sample_article_data["url"]
        assert data["title"] == sample_article_data["title"]

    def test_get_article_by_url_not_found(self, client):
        """Test getting article by non-existent URL."""
        response = client.get("/api/v1/articles/by-url/?url=https://nonexistent.com")
        assert response.status_code == 404
