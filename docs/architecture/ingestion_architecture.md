# Modular Ingestion Architecture for OneWeather

## Overview
This document outlines the modular ingestion architecture for weather forecast models (GFS, HRRR, NAM) and observational data (METAR/ASOS). The design emphasizes separation of concerns, reproducibility, and immutable data storage.

## Core Principles

1. **Modularity**: Each data source has its own connector with a common interface
2. **Immutability**: Raw data is never modified after ingestion
3. **Reproducibility**: All data transformations are deterministic and versioned
4. **Fault Tolerance**: Robust error handling and retry mechanisms
5. **Monitoring**: Comprehensive logging and metrics collection

## Architecture Components

### 1. Data Source Connectors
```
ingestion/
├── connectors/
│   ├── base_connector.py      # Abstract base class
│   ├── gfs_connector.py       # GFS-specific implementation
│   ├── hrrr_connector.py      # HRRR-specific implementation  
│   ├── nam_connector.py       # NAM-specific implementation
│   └── metar_connector.py     # METAR/ASOS implementation
```

### 2. Storage Layer
```
data/
├── raw/                       # Immutable raw data
│   ├── gfs/
│   │   ├── 2025-02-05/
│   │   │   ├── 00z/
│   │   │   │   ├── gfs.t00z.pgrb2.0p25.f000.grib2
│   │   │   │   └── metadata.json
│   │   │   └── 12z/
│   ├── hrrr/
│   ├── nam/
│   └── observations/
│       └── metar/
│           └── 2025-02-05/
│               └── 00z.json
├── processed/                 # Normalized, regridded data
└── cache/                     # Temporary working files
```

### 3. Orchestration Layer
```
ingestion/
├── scheduler.py               # Cron-based scheduling
├── download_manager.py        # Parallel download management
├── validator.py               # Data quality checks
└── notifier.py               # Alerting on failures
```

## Connector Interface Design

### BaseConnector Abstract Class
```python
class BaseConnector(ABC):
    @abstractmethod
    def fetch_data(self, cycle_time, forecast_hour, **kwargs):
        """Fetch data from source"""
        pass
    
    @abstractmethod
    def validate_data(self, data_path):
        """Validate downloaded data"""
        pass
    
    @abstractmethod
    def parse_metadata(self, data_path):
        """Extract metadata from data file"""
        pass
    
    @abstractmethod
    def get_available_cycles(self):
        """List available model cycles"""
        pass
```

### Common Methods All Connectors Must Implement
1. **Authentication** (if required)
2. **Data discovery** (list available files)
3. **Incremental download** (only fetch new data)
4. **Checksum verification** (ensure data integrity)
5. **Metadata extraction** (extract key parameters)

## GFS Connector Implementation Details

### Key Features
1. **Smart fetching**: Only download needed variables/resolutions
2. **Partial downloads**: Use HTTP range requests for large files
3. **Retry logic**: Exponential backoff for failed downloads
4. **Cache management**: Local cache to avoid re-downloads

### Configuration
```yaml
gfs:
  base_url: "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
  resolutions: ["0p25"]  # Only fetch 0.25° for CONUS
  variables: ["TMP:2 m above ground", "RH:2 m above ground", "PRES:surface"]
  forecast_hours: [0, 1, 2, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48]
  cycles: [0, 6, 12, 18]  # All 4 daily cycles
  retention_days: 14       # Keep raw data for 14 days
```

## Storage Strategy

### Immutable Raw Data Storage
1. **Directory structure**: `{source}/{date}/{cycle}/{filename}`
2. **Never modify**: Raw files are write-once, read-many
3. **Metadata alongside**: JSON files with download metadata
4. **Compression**: GZIP compression for NetCDF/text files

### Metadata Schema
```json
{
  "source": "gfs",
  "cycle_time": "2025-02-05T00:00:00Z",
  "forecast_hour": 0,
  "download_time": "2025-02-05T04:30:15Z",
  "file_size": 184567890,
  "checksum": "sha256:abc123...",
  "variables": ["2m_temperature", "surface_pressure"],
  "resolution": "0.25",
  "grid_size": "1440x721",
  "status": "validated"
}
```

### Data Lifecycle Management
1. **Hot storage**: Last 7 days on fast disk
2. **Warm storage**: 8-30 days on slower disk/object storage
3. **Cold storage**: 30+ days archived (S3 Glacier, etc.)
4. **Deletion policy**: Automatic after retention period

## Processing Pipeline

### Step 1: Ingestion
```
Source → Connector → Validation → Raw Storage
```

### Step 2: Normalization
```
Raw Storage → Variable Extraction → Regridding → Processed Storage
```

### Step 3: Quality Control
```
Processed Storage → Validation → Metrics → Alerting
```

## Error Handling and Recovery

### Failure Modes
1. **Network failures**: Retry with exponential backoff
2. **Source unavailability**: Fallback to alternative mirrors
3. **Corrupt data**: Re-download with verification
4. **Storage full**: Alert and pause ingestion

### Monitoring
1. **Download success rate** (target: >99%)
2. **Data latency** (time from model run to availability)
3. **Storage utilization** (alert at 80% capacity)
4. **Processing time** (per cycle, per forecast hour)

## Security Considerations

### Access Control
1. **Least privilege**: Connectors only need read access to sources
2. **No secrets in code**: Use environment variables or secret manager
3. **API rate limiting**: Respect source server limits

### Data Integrity
1. **Checksum verification**: SHA256 for all downloaded files
2. **Digital signatures**: Optional for critical forecasts
3. **Audit trail**: Log all data modifications

## Deployment Considerations

### Scalability
1. **Horizontal scaling**: Multiple ingestion nodes for different sources
2. **Parallel downloads**: Concurrent downloads within rate limits
3. **Batch processing**: Process multiple forecast hours in parallel

### Resource Requirements
- **CPU**: Moderate (GRIB/NetCDF parsing)
- **Memory**: 4-8GB per concurrent process
- **Storage**: 1-2TB for 14-day raw data retention
- **Network**: 100Mbps+ for timely downloads

## Testing Strategy

### Unit Tests
- Mock HTTP responses for connector tests
- Test validation logic with sample data
- Verify metadata extraction

### Integration Tests
- End-to-end ingestion with test data
- Storage layer integration
- Error recovery scenarios

### Performance Tests
- Download speed benchmarks
- Memory usage under load
- Concurrent processing limits

## Future Extensions

### Planned Enhancements
1. **Additional sources**: ECMWF, CMC, JMA models
2. **Real-time streaming**: WebSocket connections for rapid updates
3. **Machine learning**: Anomaly detection on ingestion patterns
4. **Data lineage**: Track provenance through processing pipeline

### Integration Points
1. **Alerting system**: Slack/Email/PagerDuty integration
2. **Monitoring dashboard**: Grafana/Prometheus metrics
3. **Data catalog**: Metadata search and discovery
4. **API gateway**: External access to processed data