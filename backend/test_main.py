"""
Unit Tests - Phase 3.1 Testing Framework

Tests for core API endpoints, data validation, and business logic.
"""

import pytest


class TestHealthEndpoint:
    """Health check endpoint tests"""

    @pytest.mark.unit
    def test_health_check_success(self, client):
        """✅ Health endpoint returns correct status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0-complete"
        assert "services" in data

    @pytest.mark.unit
    def test_health_services_info(self, client):
        """✅ Health endpoint lists all services"""
        response = client.get("/health")
        data = response.json()
        services = data["services"]
        assert "supabase" in services
        assert "gemini" in services
        assert "redis" in services
        assert "pose_engine" in services


class TestMetricsValidation:
    """Metrics data validation tests"""

    @pytest.mark.unit
    def test_valid_metrics(self, sample_metrics_data):
        """✅ Valid metrics pass validation"""
        from schemas import MetricsData

        metrics = MetricsData(**sample_metrics_data)
        assert metrics.angles["knee"] == 85.3
        assert metrics.pose_confidence == 0.95

    @pytest.mark.unit
    def test_invalid_pose_confidence_high(self, sample_metrics_data):
        """❌ Pose confidence > 1.0 fails"""
        from schemas import MetricsData

        sample_metrics_data["pose_confidence"] = 1.5
        with pytest.raises(ValueError):
            MetricsData(**sample_metrics_data)

    @pytest.mark.unit
    def test_invalid_pose_confidence_negative(self, sample_metrics_data):
        """❌ Negative pose confidence fails"""
        from schemas import MetricsData

        sample_metrics_data["pose_confidence"] = -0.1
        with pytest.raises(ValueError):
            MetricsData(**sample_metrics_data)

    @pytest.mark.unit
    def test_missing_angles(self, sample_metrics_data):
        """❌ Missing angles field fails"""
        from schemas import MetricsData

        del sample_metrics_data["angles"]
        with pytest.raises(ValueError):
            MetricsData(**sample_metrics_data)


class TestFeedbackEndpoint:
    """Generate feedback endpoint tests"""

    @pytest.mark.unit
    def test_feedback_request_success(self, client, sample_feedback_request):
        """✅ Valid feedback request succeeds"""
        response = client.post("/generate-feedback", json=sample_feedback_request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["completed", "cached"]
        assert "analysis_id" in data
        assert "coach_feedback" in data

    @pytest.mark.unit
    def test_feedback_response_structure(self, client, sample_feedback_request):
        """✅ Feedback response has correct structure"""
        response = client.post("/generate-feedback", json=sample_feedback_request)
        data = response.json()

        # Check required fields
        assert "summary" in data
        assert "coach_feedback" in data
        assert "performance_metrics" in data

        # Check coach feedback structure
        feedback = data["coach_feedback"]
        assert {"issue", "reason", "fix"} <= set(feedback.keys())

    @pytest.mark.unit
    def test_feedback_invalid_exercise(self, client, sample_feedback_request):
        """✅ Invalid exercise type is accepted but logged"""
        sample_feedback_request["exercise_type"] = "invalid_exercise_xyz"
        response = client.post("/generate-feedback", json=sample_feedback_request)
        # Should still succeed (warning logged)
        assert response.status_code in [200, 400]

    @pytest.mark.unit
    def test_feedback_missing_metrics(self, client):
        """❌ Missing metrics field fails"""
        request_data = {"exercise_type": "squat", "user_id": "test-user"}
        response = client.post("/generate-feedback", json=request_data)
        assert response.status_code == 422  # Validation error


class TestProfileEndpoint:
    """Profile sync endpoint tests"""

    @pytest.mark.unit
    def test_profile_sync_success(self, client, sample_profile, mock_supabase):
        """✅ Profile sync succeeds"""
        response = client.post("/sync-profile", json=sample_profile)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.unit
    def test_profile_required_fields(self, client):
        """❌ Missing required profile fields fail"""
        invalid_profile = {
            "name": "John",
            "email": "john@example.com",
            # Missing 'id'
        }
        response = client.post("/sync-profile", json=invalid_profile)
        assert response.status_code == 422


class TestSessionEndpoint:
    """Session sync endpoint tests"""

    @pytest.mark.unit
    def test_session_sync_success(self, client, sample_session, mock_supabase):
        """✅ Session sync succeeds"""
        response = client.post("/sync-session", json=sample_session)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.unit
    def test_session_invalid_reps(self, client, sample_session):
        """❌ Negative reps fail"""
        sample_session["reps"] = -5
        response = client.post("/sync-session", json=sample_session)
        assert response.status_code == 422

    @pytest.mark.unit
    def test_session_invalid_score(self, client, sample_session):
        """❌ Score > 100 fails"""
        sample_session["score"] = 150
        response = client.post("/sync-session", json=sample_session)
        assert response.status_code == 422


class TestRateLimiting:
    """Rate limiting tests - Phase 2.1"""

    @pytest.mark.unit
    def test_rate_limit_enforcement(self, client, sample_feedback_request):
        """⏱️ Rate limiting enforced after threshold"""
        # Make 11 requests (limit is 10/minute)
        for i in range(11):
            response = client.post("/generate-feedback", json=sample_feedback_request)
            if i < 10:
                assert response.status_code == 200
            else:
                # 11th request should be rate limited
                assert response.status_code == 429


class TestErrorHandling:
    """Error handling tests"""

    @pytest.mark.unit
    def test_invalid_endpoint(self, client):
        """✅ Invalid endpoint returns index.html (SPA routing)"""
        response = client.get("/nonexistent-endpoint")
        # SPA with catch-all routing serves index.html for undefined routes
        assert response.status_code == 200

    @pytest.mark.unit
    def test_invalid_method(self, client):
        """❌ Wrong HTTP method returns error"""
        response = client.put("/generate-feedback")
        assert response.status_code in [404, 405]

    @pytest.mark.unit
    def test_malformed_json(self, client):
        """❌ Malformed JSON returns error"""
        response = client.post(
            "/generate-feedback",
            data="{invalid json}",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [400, 422]


class TestCacheManager:
    """Cache functionality tests - Phase 2.5"""

    @pytest.mark.unit
    def test_cache_set_and_get(self, mock_cache):
        """✅ Cache set/get works"""
        mock_cache.set("test_key", {"data": "test_value"})
        result = mock_cache.get("test_key")
        assert result == {"data": "test_value"}

    @pytest.mark.unit
    def test_cache_miss(self, mock_cache):
        """✅ Cache miss returns None"""
        result = mock_cache.get("nonexistent_key")
        assert result is None

    @pytest.mark.unit
    def test_cache_delete(self, mock_cache):
        """✅ Cache delete works"""
        mock_cache.set("temp_key", {"temp": "data"})
        mock_cache.delete("temp_key")
        result = mock_cache.get("temp_key")
        assert result is None


class TestAPIKeyManagement:
    """API key management tests - Phase 2.1"""

    @pytest.mark.unit
    def test_api_key_generation(self):
        """✅ API key generation works"""
        from security import APIKeyManager

        key_id, key_token = APIKeyManager.generate_key("test-key")
        assert key_id.startswith("key_")
        assert len(key_token) > 20

    @pytest.mark.unit
    def test_api_key_validation(self):
        """✅ API key validation works"""
        from security import APIKeyManager

        key_id, key_token = APIKeyManager.generate_key("test-key-2")
        key_data = APIKeyManager.validate_key(key_token)
        assert key_data is not None
        assert key_data["id"] == key_id

    @pytest.mark.unit
    def test_invalid_api_key(self):
        """❌ Invalid API key returns None"""
        from security import APIKeyManager

        key_data = APIKeyManager.validate_key("invalid_token_xyz")
        assert key_data is None

    @pytest.mark.unit
    def test_api_key_revocation(self):
        """✅ Revoked API key is invalid"""
        from security import APIKeyManager

        key_id, key_token = APIKeyManager.generate_key("revoke-test")
        APIKeyManager.revoke_key(key_id)
        key_data = APIKeyManager.validate_key(key_token)
        assert key_data is None


class TestSecurityHeaders:
    """Security headers tests - Phase 2.3"""

    @pytest.mark.unit
    def test_security_headers_present(self, client):
        """✅ Security headers are present in responses"""
        response = client.get("/health")

        # Check for critical security headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "Content-Security-Policy" in response.headers

    @pytest.mark.unit
    def test_hsts_header(self, client):
        """✅ HSTS header configured"""
        response = client.get("/health")
        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is not None
        assert "max-age" in hsts


class TestRequestValidation:
    """Request validation tests - Phase 2.2"""

    @pytest.mark.unit
    def test_request_size_validation(self):
        """✅ Request size validation works"""
        from security import RequestValidator

        is_valid, error = RequestValidator.validate_request_size("/generate-feedback", 1000)
        assert is_valid is True

    @pytest.mark.unit
    def test_oversized_request(self):
        """❌ Oversized request fails validation"""
        from security import RequestValidator

        # 6MB > 5MB limit for /generate-feedback
        is_valid, error = RequestValidator.validate_request_size("/generate-feedback", 6 * 1024 * 1024)
        assert is_valid is False
        assert error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
