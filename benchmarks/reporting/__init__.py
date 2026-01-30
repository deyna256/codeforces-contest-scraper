"""Reporting module for benchmark results."""

from benchmarks.reporting.base_metrics import BenchmarkMetrics
from benchmarks.reporting.console_output import print_comparison_table
from benchmarks.reporting.html_report import generate_html_report
from benchmarks.reporting.json_report import generate_comparison_report

__all__ = [
    "BenchmarkMetrics",
    "print_comparison_table",
    "generate_html_report",
    "generate_comparison_report",
]
