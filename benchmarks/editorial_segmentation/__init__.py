"""Editorial segmentation benchmark module."""

from benchmarks.editorial_segmentation.metrics import (
    SegmentationTestResult,
    calculate_segmentation_metrics,
)
from benchmarks.editorial_segmentation.runner import SegmentationRunner
from benchmarks.editorial_segmentation.test_data import (
    SEGMENTATION_TEST_CASES,
    SegmentationTestCase,
)

__all__ = [
    "SegmentationRunner",
    "SegmentationTestResult",
    "calculate_segmentation_metrics",
    "SegmentationTestCase",
    "SEGMENTATION_TEST_CASES",
]
