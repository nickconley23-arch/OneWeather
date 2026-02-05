# OneWeather Data Ingestion

This directory contains the data ingestion pipeline for the OneWeather platform.

## Current Status: Proof-of-Concept

We have implemented a proof-of-concept for GFS data ingestion with the following features:

### ✅ Completed
1. **GFS Data Source Research**: Comprehensive documentation of NOAA/NCEP GFS data access
2. **Modular Architecture Design**: Connector-based design for multiple data sources
3. **GFS POC Implementation**: Python script to download and inspect GFS forecast files
4. **Immutable Storage Strategy**: Design for write-once, read-many raw data storage

### 📁 Directory Structure
```
ingestion/
├── gfs_poc.py              # Main GFS ingestion proof-of-concept
├── test_gfs_poc.py         # Unit tests for the POC
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── (future)
    ├── connectors/        # Modular connector implementations
    ├── scheduler.py       # Cron-based scheduling
    ├── validator.py       # Data quality checks
    └── notifier.py       # Alerting system
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install wgrib2 (for GRIB2 inspection)
```bash
# Ubuntu/Debian
sudo apt-get install wgrib2

# Or via conda
conda install -c conda-forge wgrib2
```

### 3. Run the GFS POC
```bash
# List available cycles for today
python gfs_poc.py --list-cycles

# Download a specific forecast (today's 00Z analysis)
python gfs_poc.py --cycle 00 --forecast-hour 0

# Download with custom parameters
python gfs_poc.py --date 20250205 --cycle 12 --forecast-hour 24 --resolution 0p50
```

### 4. Run Tests
```bash
python test_gfs_poc.py
```

## Architecture Overview

### Connector Pattern
Each data source (GFS, HRRR, NAM, METAR) will have its own connector implementing a common interface:

```python
class BaseConnector:
    def fetch_data(self, cycle_time, forecast_hour, **kwargs): ...
    def validate_data(self, data_path): ...
    def parse_metadata(self, data_path): ...
```

### Storage Layout
```
data/
├── raw/                    # Immutable raw data
│   ├── gfs/
│   │   ├── 2025-02-05/
│   │   │   ├── 00z/
│   │   │   │   ├── gfs.t00z.pgrb2.0p25.f000.grib2
│   │   │   │   └── metadata.json
├── processed/             # Normalized, regridded data
└── metadata/              # Comprehensive metadata
```

## Next Steps

### Immediate (Week 1)
1. [ ] Test GFS POC with actual data download
2. [ ] Implement basic error handling and retry logic
3. [ ] Add configuration management (YAML config files)
4. [ ] Create Docker container for reproducible environment

### Short-term (Week 2-3)
1. [ ] Implement HRRR connector
2. [ ] Implement NAM connector  
3. [ ] Design and implement METAR/ASOS observation ingestion
4. [ ] Add scheduling system (cron/APScheduler)

### Medium-term (Month 1-2)
1. [ ] Implement data validation pipeline
2. [ ] Add monitoring and alerting
3. [ ] Implement storage lifecycle management
4. [ ] Create data quality metrics

## Configuration

### Environment Variables
```bash
export ONEWEATHER_DATA_DIR="/home/ubuntu/OneWeather/data"
export ONEWEATHER_LOG_LEVEL="INFO"
export NOMADS_RATE_LIMIT="10"  # requests per minute
```

### Configuration File (config.yaml)
```yaml
gfs:
  base_url: "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
  resolutions: ["0p25"]
  variables: ["TMP:2 m above ground", "RH:2 m above ground"]
  forecast_hours: [0, 1, 2, 3, 6, 9, 12, 15, 18, 21, 24]
  cycles: [0, 6, 12, 18]
  
storage:
  raw_retention_days: 30
  processed_retention_days: 90
  compression: "gzip"
  
logging:
  level: "INFO"
  file: "/var/log/oneweather/ingestion.log"
```

## Development

### Code Style
- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Document all public functions with docstrings
- Write unit tests for new functionality

### Testing
```bash
# Run all tests
pytest test_gfs_poc.py -v

# Run with coverage
pytest test_gfs_poc.py --cov=. --cov-report=html
```

### Contributing
1. Create a feature branch
2. Write tests for new functionality
3. Ensure all tests pass
4. Update documentation
5. Submit pull request

## Troubleshooting

### Common Issues

1. **wgrib2 not found**
   ```
   Error: wgrib2 command not found
   ```
   Solution: Install wgrib2 via apt or conda

2. **Download timeout**
   ```
   requests.exceptions.Timeout
   ```
   Solution: Increase timeout in configuration or check network connectivity

3. **File already exists**
   ```
   FileExistsError: File already exists
   ```
   Solution: The system enforces immutability. Use `--force` flag (not yet implemented) or delete file manually if corrupted.

4. **Memory error with large files**
   ```
   MemoryError
   ```
   Solution: Process files in chunks, increase system memory, or use lower resolution data.

## Resources

### Documentation
- [GFS Data Source Documentation](../docs/data_sources/GFS.md)
- [Ingestion Architecture](../docs/architecture/ingestion_architecture.md)
- [Storage Strategy](../docs/architecture/storage_strategy.md)

### External Links
- [NOAA NOMADS Server](https://nomads.ncep.noaa.gov/)
- [GFS Product Description](https://www.nco.ncep.noaa.gov/pmb/products/gfs/)
- [wgrib2 Documentation](https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/)

### Tools
- [Herbie: Smart GFS Downloader](https://github.com/blaylockbk/Herbie)
- [cfgrib: GRIB2 Python Interface](https://github.com/ecmwf/cfgrib)
- [xarray: N-D labeled arrays](https://xarray.pydata.org/)