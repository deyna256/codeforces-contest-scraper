"""Benchmark type definitions."""

from enum import Enum


class BenchmarkType(Enum):
    """Types of benchmarks supported by the system."""

    EDITORIAL_FINDER = "editorial_finder"
    EDITORIAL_SEGMENTATION = "editorial_segmentation"
