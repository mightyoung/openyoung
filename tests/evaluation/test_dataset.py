"""
Evaluation Dataset Tests
"""

import pytest
from src.evaluation.dataset import (
    EVALUATION_DATASET,
    EvalTestCase,
    get_test_case_by_id,
    get_test_cases_by_difficulty,
    get_test_cases_by_type,
    get_dataset_stats,
)


class TestEvalTestCase:
    """Test EvalTestCase dataclass"""

    def test_testcase_creation(self):
        tc = EvalTestCase(
            id="test_001",
            task_type="coding",
            task_description="Test task",
            expected_outputs={"result": "test"},
            success_criteria=["criteria1"],
            difficulty="easy",
            domain="技术",
        )
        assert tc.id == "test_001"
        assert tc.task_type == "coding"
        assert tc.difficulty == "easy"


class TestEvaluationDataset:
    """Test evaluation dataset functions"""

    def test_dataset_not_empty(self):
        assert len(EVALUATION_DATASET) > 0

    def test_get_test_cases_by_type_coding(self):
        coding_cases = get_test_cases_by_type("coding")
        assert len(coding_cases) > 0
        for tc in coding_cases:
            assert tc.task_type == "coding"

    def test_get_test_cases_by_type_general(self):
        general_cases = get_test_cases_by_type("general")
        assert len(general_cases) > 0
        for tc in general_cases:
            assert tc.task_type == "general"

    def test_get_test_cases_by_type_research(self):
        research_cases = get_test_cases_by_type("research")
        assert len(research_cases) > 0
        for tc in research_cases:
            assert tc.task_type == "research"

    def test_get_test_cases_by_difficulty_easy(self):
        easy_cases = get_test_cases_by_difficulty("easy")
        assert len(easy_cases) > 0
        for tc in easy_cases:
            assert tc.difficulty == "easy"

    def test_get_test_cases_by_difficulty_medium(self):
        medium_cases = get_test_cases_by_difficulty("medium")
        assert len(medium_cases) > 0
        for tc in medium_cases:
            assert tc.difficulty == "medium"

    def test_get_test_cases_by_difficulty_hard(self):
        hard_cases = get_test_cases_by_difficulty("hard")
        assert len(hard_cases) > 0
        for tc in hard_cases:
            assert tc.difficulty == "hard"

    def test_get_test_case_by_id_exists(self):
        tc = get_test_case_by_id("code_001")
        assert tc is not None
        assert tc.id == "code_001"

    def test_get_test_case_by_id_not_exists(self):
        tc = get_test_case_by_id("nonexistent_id")
        assert tc is None

    def test_get_dataset_stats(self):
        stats = get_dataset_stats()
        assert "total" in stats
        assert "by_type" in stats
        assert "by_difficulty" in stats
        assert "by_domain" in stats
        assert stats["total"] == len(EVALUATION_DATASET)

    def test_get_dataset_stats_by_type(self):
        stats = get_dataset_stats()
        # Verify by_type has expected task types
        assert "coding" in stats["by_type"]
        assert "general" in stats["by_type"]

    def test_get_dataset_stats_by_difficulty(self):
        stats = get_dataset_stats()
        # Verify by_difficulty has expected difficulties
        assert "easy" in stats["by_difficulty"]
        assert "medium" in stats["by_difficulty"]
        assert "hard" in stats["by_difficulty"]

    def test_all_cases_have_required_fields(self):
        """All test cases should have required fields"""
        for tc in EVALUATION_DATASET:
            assert tc.id is not None
            assert tc.task_type is not None
            assert tc.task_description is not None
            assert tc.expected_outputs is not None
            assert tc.success_criteria is not None
            assert tc.difficulty in ["easy", "medium", "hard"]
            assert tc.domain is not None
