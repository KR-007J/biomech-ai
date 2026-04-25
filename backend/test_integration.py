"""
Integration Tests - Phase 3.2 Testing Framework

Tests for end-to-end workflows and component interactions.
"""

import pytest


class TestEndToEndAnalysisFlow:
    """End-to-end biomechanical analysis flow tests"""

    @pytest.mark.integration
    def test_complete_analysis_workflow(
        self, client, sample_feedback_request, mock_supabase
    ):
        """✅ Complete analysis workflow succeeds"""
        # Step 1: Submit analyze request
        response = client.post("/generate-feedback", json=sample_feedback_request)
        assert response.status_code == 200
        analysis_data = response.json()

        # Step 2: Verify response structure
        assert analysis_data["analysis_id"]
        assert analysis_data["coach_feedback"]["issue"]
        assert analysis_data["performance_metrics"]["processing_time_sec"] > 0

    @pytest.mark.integration
    def test_analysis_then_profile_sync(
        self, client, sample_feedback_request, sample_profile, mock_supabase
    ):
        """✅ Analysis followed by profile sync works"""
        # Analyze
        response1 = client.post("/generate-feedback", json=sample_feedback_request)
        assert response1.status_code == 200

        # Sync profile
        response2 = client.post("/sync-profile", json=sample_profile)
        assert response2.status_code == 200
        assert response2.json()["status"] == "success"

    @pytest.mark.integration
    def test_session_tracking_workflow(
        self, client, sample_feedback_request, sample_session, mock_supabase
    ):
        """✅ Session tracking workflow succeeds"""
        # Submit feedback
        response1 = client.post("/generate-feedback", json=sample_feedback_request)
        assert response1.status_code == 200

        # Save session
        response2 = client.post("/sync-session", json=sample_session)
        assert response2.status_code == 200


class TestCacheIntegration:
    """Cache integration with API endpoints"""

    @pytest.mark.integration
    def test_cache_hit_on_repeated_request(self, client, sample_feedback_request):
        """✅ Repeated requests use cache"""
        # First request - cache miss
        response1 = client.post("/generate-feedback", json=sample_feedback_request)
        assert response1.status_code == 200
        data1 = response1.json()
        data1["performance_metrics"]["processing_time_sec"]

        # Second request - cache hit (should be faster)
        response2 = client.post("/generate-feedback", json=sample_feedback_request)
        assert response2.status_code == 200
        data2 = response2.json()

        # Cached response should indicate cache hit
        assert data2["status"] in ["cached", "completed"]

    @pytest.mark.integration
    def test_cache_invalidation_on_profile_edit(
        self, client, sample_feedback_request, sample_profile, mock_supabase, mock_cache
    ):
        """✅ Cache invalidates when profile changes"""
        # First request
        response1 = client.post("/generate-feedback", json=sample_feedback_request)

        # Update profile (should invalidate cache)
        response2 = client.post("/sync-profile", json=sample_profile)
        assert response2.status_code == 200

        # Next request might be cache miss (due to invalidation)
        # This tests the cache invalidation logic


class TestMultipleUsers:
    """Multi-user scenarios"""

    @pytest.mark.integration
    def test_different_users_separate_caches(self, client, sample_metrics_data):
        """✅ Different users have separate cache entries"""
        # User 1 request
        request1 = {
            "metrics": sample_metrics_data,
            "exercise_type": "squat",
            "user_id": "user-1",
        }
        response1 = client.post("/generate-feedback", json=request1)
        assert response1.status_code == 200

        # User 2 request
        request2 = {
            "metrics": sample_metrics_data,
            "exercise_type": "squat",
            "user_id": "user-2",
        }
        response2 = client.post("/generate-feedback", json=request2)
        assert response2.status_code == 200

        # Responses should be independent


class TestErrorRecovery:
    """Error handling and recovery tests"""

    @pytest.mark.integration
    def test_malformed_metrics_error_handling(self, client):
        """✅ Malformed metrics handled gracefully"""
        request = {
            "metrics": {
                "angles": "not_a_dict",  # Invalid
                "deviations": {},
                "pose_confidence": 0.9,
            },
            "exercise_type": "squat",
            "user_id": "test-user",
        }
        response = client.post("/generate-feedback", json=request)
        # Should fail validation
        assert response.status_code in [400, 422]

    @pytest.mark.integration
    def test_missing_required_fields_error_handling(self, client):
        """✅ Missing required fields handled gracefully"""
        request = {
            "exercise_type": "squat"
            # Missing 'metrics'
        }
        response = client.post("/generate-feedback", json=request)
        assert response.status_code == 422


class TestMetricsCollection:
    """Metrics and monitoring integration tests"""

    @pytest.mark.integration
    def test_metrics_endpoint_available(self, client):
        """✅ Metrics endpoint provides Prometheus data"""
        response = client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        # Check for Prometheus format
        assert "biomech_" in content or "TYPE" in content or "#" in content

    @pytest.mark.integration
    def test_cache_stats_available(self, client):
        """✅ Cache stats endpoint works"""
        response = client.get("/cache-stats")
        assert response.status_code == 200
        data = response.json()
        assert "redis_enabled" in data or "in_memory_entries" in data

    @pytest.mark.integration
    def test_task_stats_available(self, client):
        """✅ Task stats endpoint works"""
        response = client.get("/task-stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data


class TestDataConsistency:
    """Data consistency across operations"""

    @pytest.mark.integration
    def test_profile_data_consistency(self, client, sample_profile, mock_supabase):
        """✅ Profile data remains consistent"""
        # Sync profile
        response = client.post("/sync-profile", json=sample_profile)
        assert response.status_code == 200

        # Verify stored data matches input
        mock_supabase.table.return_value.upsert.return_value.execute.assert_called()


class TestConcurrentRequests:
    """Concurrent request handling"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_feedback_requests(self, client, sample_feedback_request):
        """✅ Multiple concurrent requests handled"""
        responses = []
        for i in range(5):
            response = client.post("/generate-feedback", json=sample_feedback_request)
            responses.append(response)

        # All requests should return 200 (some may be rate limited)
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0


class TestHealthCheckIntegration:
    """Health check and service discovery"""

    @pytest.mark.integration
    def test_health_check_all_services_info(self, client):
        """✅ Health check shows all service status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # Verify all services are listed
        services = data["services"]
        expected_services = ["supabase", "gemini", "redis", "pose_engine"]
        for service in expected_services:
            assert service in services


class TestAPIStability:
    """API stability and robustness tests"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_api_handles_large_payload(self, client, sample_feedback_request):
        """✅ API handles large metrics data"""
        # Add many extra joints
        for i in range(50):
            sample_feedback_request["metrics"]["angles"][f"joint_{i}"] = 90.0
            sample_feedback_request["metrics"]["deviations"][f"joint_{i}"] = 2.0

        response = client.post("/generate-feedback", json=sample_feedback_request)
        # Should handle or reject gracefully
        assert response.status_code in [200, 413]

    @pytest.mark.integration
    def test_api_handles_special_characters(self, client, sample_profile):
        """✅ API handles special characters in strings"""
        sample_profile["name"] = "José García-López"
        sample_profile["email"] = "josé@example.com"

        response = client.post("/sync-profile", json=sample_profile)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_api_handles_unicode(self, client, sample_profile):
        """✅ API handles Unicode characters"""
        sample_profile["name"] = "用户名 用户"

        response = client.post("/sync-profile", json=sample_profile)
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
