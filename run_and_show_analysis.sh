#!/bin/bash
set -e

echo "=== building localstack resources ==="
python src/infrastructure/setup_localstack_resources.py

echo "=== Running review analysis ==="
python run_analysis.py

echo "=== Showing analysis results ==="
python show_results.py

echo "=== Analysis complete ===" 