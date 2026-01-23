"""Generate interactive HTML reports for benchmark results."""

from datetime import datetime
from pathlib import Path
from typing import Any


def generate_html_report(report_data: dict[str, Any], output_path: Path) -> Path:
    """
    Generate interactive HTML report from benchmark data.

    Args:
        report_data: Benchmark data dictionary
        output_path: Path to save HTML file

    Returns:
        Path to generated HTML file
    """
    # Generate timestamp string
    timestamp_str = report_data["benchmark_info"]["timestamp"]
    try:
        dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        formatted_date = dt.strftime("%B %d, %Y at %H:%M:%S")
    except (ValueError, KeyError):
        formatted_date = timestamp_str

    # Generate comparison table rows
    comparison_rows = []
    for i, model in enumerate(report_data["summary"]):
        rank_class = f" rank-{i + 1}" if i < 3 else ""
        accuracy_class = (
            "metric-good"
            if model["accuracy"] >= 80
            else "metric-medium"
            if model["accuracy"] >= 70
            else "metric-poor"
        )
        f1_class = (
            "metric-good"
            if model["f1_score"] >= 80
            else "metric-medium"
            if model["f1_score"] >= 70
            else "metric-poor"
        )

        # Format pricing information
        pricing_info = "N/A"
        price_class = ""
        if model.get("pricing"):
            avg_price = model["pricing"]["avg_price_per_token"]
            pricing_info = f"{avg_price:.0e}"
            # Color coding: green for cheap, yellow for medium, red for expensive
            if avg_price < 1e-6:
                price_class = "metric-good"  # Very cheap
            elif avg_price < 1e-5:
                price_class = "metric-medium"  # Medium
            else:
                price_class = ""  # Expensive (no special class)

        row = f"""<tr>
            <td><span class="rank{rank_class}">{i + 1}</span></td>
            <td><strong>{model["display_name"]}</strong><br><small style="color: #7f8c8d;">{model["model_name"]}</small></td>
            <td><span class="metric {accuracy_class}">{model["accuracy"]:.1f}%</span></td>
            <td>{model["avg_latency_ms"]:.0f}ms</td>
            <td>{model["precision"]:.1f}%</td>
            <td>{model["recall"]:.1f}%</td>
            <td><span class="metric {f1_class}">{model["f1_score"]:.1f}%</span></td>
            <td>{model["successful_tests"]}/{model["successful_tests"] + model["failed_tests"]}</td>
            <td><span class="metric {price_class}">{pricing_info}</span></td>
        </tr>"""
        comparison_rows.append(row)

    # Generate detailed results sections
    details_sections = []
    for model in report_data["summary"]:
        model_id = model["model_name"].replace("/", "-")
        accuracy_color = (
            "#27ae60"
            if model["accuracy"] >= 80
            else "#f39c12"
            if model["accuracy"] >= 70
            else "#e74c3c"
        )

        # Generate test result rows
        test_rows = []
        for test in report_data["detailed_results"][model["model_name"]]["test_results"]:
            expected_text = test["expected"] if test["expected"] else "None"
            found_text = ", ".join(test["found"]) if test["found"] else "None"

            if test["correct"]:
                result_class = "test-correct"
                result_text = "✓ Correct"
            elif test.get("error"):
                result_class = "test-error"
                result_text = "⚠ Error"
            else:
                result_class = "test-incorrect"
                result_text = "✗ Incorrect"

            test_row = f"""<tr>
                <td><span class="contest-id">{test["contest_id"]}</span></td>
                <td><small>{expected_text}</small></td>
                <td><small>{found_text}</small></td>
                <td><span class="test-result {result_class}">{result_text}</span></td>
                <td>{test["latency_ms"]:.0f}ms</td>
            </tr>"""
            test_rows.append(test_row)

        section = f"""<div class="model-details" id="model-{model_id}">
            <div class="model-name">{model["display_name"]}</div>
            <div class="metrics-row">
                <div class="metric-box">
                    <div class="metric-box-label">Accuracy</div>
                    <div class="metric-box-value" style="color: {accuracy_color}">{model["accuracy"]:.1f}%</div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-label">Avg Latency</div>
                    <div class="metric-box-value">{model["avg_latency_ms"]:.0f}ms</div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-label">F1 Score</div>
                    <div class="metric-box-value">{model["f1_score"]:.1f}%</div>
                </div>
                <div class="metric-box">
                    <div class="metric-box-label">Tests Passed</div>
                    <div class="metric-box-value">{model["successful_tests"]}/{model["successful_tests"] + model["failed_tests"]}</div>
                </div>
            </div>

            <table class="test-results-table">
                <thead>
                    <tr>
                        <th>Contest ID</th>
                        <th>Expected</th>
                        <th>Found</th>
                        <th>Result</th>
                        <th>Latency</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(test_rows)}
                </tbody>
            </table>
        </div>"""
        details_sections.append(section)

    # Generate complete HTML
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Benchmark Results - {timestamp_str}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}

        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 28px;
        }}

        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 14px;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .info-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}

        .info-label {{
            font-size: 12px;
            color: #7f8c8d;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}

        .info-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}

        h2 {{
            color: #2c3e50;
            margin: 30px 0 15px 0;
            font-size: 20px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            font-size: 14px;
        }}

        th {{
            background: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
        }}

        th:hover {{
            background: #2980b9;
        }}

        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .rank {{
            font-weight: bold;
            color: #3498db;
            font-size: 16px;
        }}

        .rank-1 {{ color: #f39c12; }}
        .rank-2 {{ color: #95a5a6; }}
        .rank-3 {{ color: #cd7f32; }}

        .metric {{
            font-weight: 600;
        }}

        .metric-good {{ color: #27ae60; }}
        .metric-medium {{ color: #f39c12; }}
        .metric-poor {{ color: #e74c3c; }}

        .test-result {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}

        .test-correct {{
            background: #d4edda;
            color: #155724;
        }}

        .test-incorrect {{
            background: #f8d7da;
            color: #721c24;
        }}

        .test-error {{
            background: #fff3cd;
            color: #856404;
        }}

        .details-section {{
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
        }}

        .model-details {{
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 6px;
            border: 1px solid #e1e8ed;
        }}

        .model-name {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
        }}

        .metrics-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }}

        .metric-box {{
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
            text-align: center;
        }}

        .metric-box-label {{
            font-size: 11px;
            color: #7f8c8d;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}

        .metric-box-value {{
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
        }}

        .test-results-table {{
            width: 100%;
            font-size: 13px;
            margin-top: 15px;
        }}

        .test-results-table th {{
            background: #34495e;
            font-size: 12px;
        }}

        .contest-id {{
            font-family: 'Courier New', monospace;
            color: #3498db;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
            }}

            h1 {{
                font-size: 22px;
            }}

            .info-grid {{
                grid-template-columns: 1fr;
            }}

            table {{
                font-size: 12px;
            }}

            th, td {{
                padding: 8px;
            }}
        }}

        .sort-indicator {{
            margin-left: 5px;
            font-size: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 LLM Model Benchmark Results</h1>
        <div class="subtitle">
            Generated on {formatted_date}
        </div>

        <div class="info-grid">
            <div class="info-card">
                <div class="info-label">Total Models</div>
                <div class="info-value">{report_data["benchmark_info"]["total_models"]}</div>
            </div>
            <div class="info-card">
                <div class="info-label">Test Cases</div>
                <div class="info-value">{report_data["benchmark_info"]["test_cases"]}</div>
            </div>
        </div>

        <h2>📊 Model Comparison</h2>
        <table id="comparisonTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Rank <span class="sort-indicator">▼</span></th>
                    <th onclick="sortTable(1)">Model</th>
                    <th onclick="sortTable(2)">Accuracy <span class="sort-indicator"></span></th>
                    <th onclick="sortTable(3)">Avg Latency <span class="sort-indicator"></span></th>
                    <th onclick="sortTable(4)">Precision <span class="sort-indicator"></span></th>
                    <th onclick="sortTable(5)">Recall <span class="sort-indicator"></span></th>
                    <th onclick="sortTable(6)">F1 Score <span class="sort-indicator"></span></th>
                    <th onclick="sortTable(7)">Success Rate <span class="sort-indicator"></span></th>
                    <th onclick="sortTable(8)">Avg Price/Token <span class="sort-indicator"></span></th>
                </tr>
            </thead>
            <tbody>
                {"".join(comparison_rows)}
            </tbody>
        </table>

        <h2>📋 Detailed Results</h2>
        <div class="details-section">
            {"".join(details_sections)}
        </div>
    </div>

    <script>
        let sortDirection = {{}};

        function sortTable(columnIndex) {{
            const table = document.getElementById('comparisonTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Toggle sort direction
            sortDirection[columnIndex] = !sortDirection[columnIndex];
            const ascending = sortDirection[columnIndex];

            // Update sort indicators
            document.querySelectorAll('.sort-indicator').forEach(el => el.textContent = '');
            const th = table.querySelectorAll('th')[columnIndex];
            const indicator = th.querySelector('.sort-indicator');
            if (indicator) {{
                indicator.textContent = ascending ? '▲' : '▼';
            }}

            rows.sort((a, b) => {{
                let aValue = a.children[columnIndex].textContent.trim();
                let bValue = b.children[columnIndex].textContent.trim();

                // Extract numeric values
                aValue = parseFloat(aValue.replace(/[^0-9.-]/g, '')) || aValue;
                bValue = parseFloat(bValue.replace(/[^0-9.-]/g, '')) || bValue;

                if (typeof aValue === 'number' && typeof bValue === 'number') {{
                    return ascending ? aValue - bValue : bValue - aValue;
                }}

                return ascending
                    ? String(aValue).localeCompare(String(bValue))
                    : String(bValue).localeCompare(String(aValue));
            }});

            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));

            // Update rank numbers
            rows.forEach((row, index) => {{
                const rankCell = row.querySelector('.rank');
                rankCell.textContent = index + 1;
                rankCell.className = 'rank' + (index < 3 ? ` rank-${{index + 1}}` : '');
            }});
        }}
    </script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path
