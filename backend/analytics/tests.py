from django.test import TestCase
from analytics.ml_engine import get_engagement_label

class EngagementTest(TestCase):
    def test_labels(self):
        self.assertEqual(get_engagement_label(80), "high")
        self.assertEqual(get_engagement_label(60), "medium")
        self.assertEqual(get_engagement_label(20), "low")

from unittest.mock import patch, MagicMock
from analytics.ml_engine import compute_risk_score

class AtRiskTest(TestCase):
    @patch('analytics.ml_engine.CourseEnrollment.objects.get')
    @patch('analytics.ml_engine.LearningEvent.objects.filter')
    def test_risk_score_no_enrollment(self, mock_filter, mock_get):
        from courses.models import CourseEnrollment
        mock_get.side_effect = CourseEnrollment.DoesNotExist
        
        result = compute_risk_score(MagicMock(), MagicMock())
        self.assertEqual(result["risk_score"], 0.0)
        self.assertEqual(result["risk_level"], "low")

from analytics.ml_engine import compute_video_heatmap

class HeatmapTest(TestCase):
    @patch('analytics.ml_engine.LearningEvent.objects.filter')
    def test_heatmap_empty(self, mock_filter):
        mock_filter.return_value.values.return_value = []
        result = compute_video_heatmap(MagicMock())
        self.assertEqual(result, [])


# ===========================================================================
# Tests cho Dropout Predictor (Tính năng B)
# ===========================================================================

import numpy as np
from analytics.dropout_predictor import extract_features, predict_dropout


class DropoutExtractFeaturesTest(TestCase):
    """Test extract_features trả đúng shape (9,)."""

    @patch('analytics.dropout_predictor.LearningEvent.objects.filter')
    def test_extract_features_shape(self, mock_filter):
        """Feature vector phải có 9 chiều."""
        from django.utils import timezone
        from datetime import timedelta

        # Mock enrollment
        enrollment = MagicMock()
        enrollment.last_accessed_at = timezone.now() - timedelta(days=2)
        enrollment.course_progress_percent = 45.0
        enrollment.login_streak = 3
        enrollment.enrolled_at = timezone.now() - timedelta(days=10)
        enrollment.student = MagicMock()
        enrollment.course = MagicMock()

        # Mock events queryset
        mock_qs = MagicMock()
        mock_qs.count.return_value = 20
        mock_qs.filter.return_value.count.return_value = 3
        mock_qs.exclude.return_value.values_list.return_value = [1.0, 1.25, 1.5]

        features = extract_features(enrollment, mock_qs)

        self.assertIsInstance(features, np.ndarray)
        self.assertEqual(features.shape, (9,))

    @patch('analytics.dropout_predictor.LearningEvent.objects.filter')
    def test_extract_features_zero_events(self, mock_filter):
        """Khi không có event nào, ratios nên là 0."""
        from django.utils import timezone
        from datetime import timedelta

        enrollment = MagicMock()
        enrollment.last_accessed_at = None  # Chưa từng truy cập
        enrollment.course_progress_percent = 0.0
        enrollment.login_streak = 0
        enrollment.enrolled_at = timezone.now() - timedelta(days=5)
        enrollment.student = MagicMock()
        enrollment.course = MagicMock()

        mock_qs = MagicMock()
        mock_qs.count.return_value = 0
        mock_qs.filter.return_value.count.return_value = 0
        mock_qs.exclude.return_value.values_list.return_value = []

        features = extract_features(enrollment, mock_qs)

        self.assertEqual(features.shape, (9,))
        self.assertEqual(features[0], 30)       # days_inactive = 30 khi null
        self.assertEqual(features[3], 0.0)      # skip_fwd_ratio = 0
        self.assertEqual(features[5], 0.0)      # note_ratio = 0
        self.assertEqual(features[6], 1.0)      # avg_playback_rate default 1.0


class DropoutPredictFallbackTest(TestCase):
    """Test predict_dropout fallback khi chưa có model."""

    @patch('analytics.dropout_predictor._load_model')
    @patch('analytics.ml_engine.compute_risk_score')
    def test_fallback_to_rule_based(self, mock_risk, mock_load):
        """Khi chưa có model pkl, phải fallback về rule-based."""
        mock_load.return_value = (None, None)
        mock_risk.return_value = {
            "risk_score": 55.0,
            "risk_level": "medium",
            "reasons": ["Test reason"],
        }

        enrollment = MagicMock()
        enrollment.student = MagicMock()
        enrollment.course = MagicMock()

        result = predict_dropout(enrollment)

        self.assertEqual(result["model_type"], "rule-based")
        self.assertEqual(result["risk_score"], 55.0)
        self.assertIsNone(result["dropout_probability"])


class DropoutPredictWithModelTest(TestCase):
    """Test predict_dropout khi có model."""

    @patch('analytics.dropout_predictor._load_model')
    @patch('analytics.dropout_predictor.extract_features')
    def test_predict_with_model(self, mock_extract, mock_load):
        """Khi có model, phải trả model_type='random_forest' và dropout_probability."""
        # Mock model
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.array([[0.3, 0.7]])

        # Mock scaler
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.array([[0.1] * 9])

        mock_load.return_value = (mock_model, mock_scaler)
        mock_extract.return_value = np.array([5, 30, 1, 0.2, 0.05, 0.0, 1.5, 0.5, 2.0])

        enrollment = MagicMock()
        result = predict_dropout(enrollment)

        self.assertEqual(result["model_type"], "random_forest")
        self.assertAlmostEqual(result["dropout_probability"], 0.7, places=2)
        self.assertEqual(result["risk_score"], 70.0)
        self.assertEqual(result["risk_level"], "high")


# ===========================================================================
# Tests cho Recommender (Tính năng C)
# ===========================================================================

from analytics.recommender import get_similar_videos

class RecommenderTest(TestCase):
    def test_get_similar_videos_empty(self):
        self.assertEqual(get_similar_videos(1, None, {}), [])
        
    def test_get_similar_videos_small_data(self):
        import numpy as np
        M = np.zeros((2, 2))
        video_idx = {1: 0, 2: 1}
        self.assertEqual(get_similar_videos(1, M, video_idx), [])
        
    def test_get_similar_videos_mock(self):
        import numpy as np
        M = np.array([
            [1.0, 0.9, 0.1],
            [0.8, 1.0, 0.2],
            [0.1, 0.2, 1.0],
            [0.9, 0.8, 0.3],
        ])
        video_idx = {10: 0, 20: 1, 30: 2}
        result = get_similar_videos(10, M, video_idx, n=2)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]['video_id'], 20)
