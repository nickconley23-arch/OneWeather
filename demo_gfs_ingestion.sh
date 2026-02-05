#!/bin/bash
# Demonstration script for GFS data ingestion proof-of-concept

echo "================================================"
echo "OneWeather GFS Data Ingestion Demonstration"
echo "================================================"
echo ""

# Set up environment
cd /home/ubuntu/OneWeather

echo "1. Checking Python environment..."
python3 --version
echo ""

echo "2. Running unit tests..."
cd ingestion
python3 test_gfs_poc.py
echo ""

echo "3. Showing directory structure..."
echo "Data directory will be created at: /home/ubuntu/OneWeather/data"
echo ""
echo "Expected structure after running:"
echo "data/"
echo "├── raw/"
echo "│   └── gfs/"
echo "│       └── $(date +%Y%m%d)/"
echo "│           └── 00z/"
echo "│               ├── gfs.t00z.pgrb2.0p25.f000.grib2"
echo "│               └── metadata.json"
echo "└── metadata/"
echo "    └── gfs/"
echo "        └── $(date +%Y%m%d)/"
echo "            └── 00z/"
echo "                └── gfs.t00z.pgrb2.0p25.f000.json"
echo ""

echo "4. Checking available GFS cycles (dry run)..."
python3 gfs_poc.py --list-cycles
echo ""

echo "5. To actually download a GFS forecast file, run:"
echo "   python3 gfs_poc.py --cycle 00 --forecast-hour 0"
echo ""
echo "   Or with custom date:"
echo "   python3 gfs_poc.py --date $(date +%Y%m%d) --cycle 12 --forecast-hour 24"
echo ""

echo "6. Installation instructions:"
echo "   a) Install Python dependencies:"
echo "      pip install -r requirements.txt"
echo ""
echo "   b) Install wgrib2 for GRIB2 inspection:"
echo "      sudo apt-get install wgrib2"
echo "      # or: conda install -c conda-forge wgrib2"
echo ""

echo "================================================"
echo "Documentation available:"
echo "- GFS Data Source: docs/data_sources/GFS.md"
echo "- Architecture: docs/architecture/ingestion_architecture.md"
echo "- Storage Strategy: docs/architecture/storage_strategy.md"
echo "- Usage: ingestion/README.md"
echo "================================================"