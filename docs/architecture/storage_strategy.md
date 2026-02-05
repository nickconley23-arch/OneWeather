# Immutable Raw Data Storage Strategy

## Overview
This document outlines the storage strategy for raw weather data in the OneWeather platform. The core principle is **immutability** - once data is ingested, it is never modified. This ensures reproducibility and traceability of all forecasts and analyses.

## Storage Hierarchy

### 1. Raw Data Storage (Immutable)
```
data/raw/
├── gfs/
│   ├── 2025-02-05/
│   │   ├── 00z/
│   │   │   ├── gfs.t00z.pgrb2.0p25.f000.grib2
│   │   │   ├── gfs.t00z.pgrb2.0p25.f001.grib2
│   │   │   └── metadata.json
│   │   ├── 06z/
│   │   ├── 12z/
│   │   └── 18z/
│   ├── 2025-02-06/
│   └── ...
├── hrrr/
├── nam/
└── observations/
    ├── metar/
    │   ├── 2025-02-05/
    │   │   ├── 00z.json
    │   │   ├── 01z.json
    │   │   └── ...
    │   └── ...
    └── asos/
```

### 2. Processed Data Storage (Derived)
```
data/processed/
├── normalized/
│   ├── gfs/
│   │   ├── 2025-02-05/
│   │   │   ├── 00z/
│   │   │   │   ├── temperature_h3.parquet
│   │   │   │   ├── pressure_h3.parquet
│   │   │   │   └── metadata.json
│   │   │   └── ...
│   │   └── ...
├── regridded/
└── aggregated/
```

### 3. Metadata Storage
```
data/metadata/
├── gfs/
│   ├── 2025-02-05/
│   │   ├── 00z/
│   │   │   ├── gfs.t00z.pgrb2.0p25.f000.json
│   │   │   └── ...
│   │   └── ...
│   └── index.json
├── hrrr/
└── ...
```

### 4. Cache Storage (Temporary)
```
data/cache/
├── downloads/
├── processing/
└── tmp/
```

## Immutability Principles

### 1. Write-Once, Read-Many (WORM)
- Raw files are never modified after ingestion
- If data needs correction, create new version with different filename
- Use checksums to detect corruption

### 2. Versioning Strategy
```
# For corrected data:
gfs.t00z.pgrb2.0p25.f000.v1.grib2  # Original
gfs.t00z.pgrb2.0p25.f000.v2.grib2  # Corrected
```

### 3. Deletion Policy
- Raw data: Keep for 30 days minimum
- Processed data: Keep for 90 days minimum  
- Metadata: Keep indefinitely
- Automatic cleanup based on retention policy

## File Naming Conventions

### Raw Data Files
```
{model}.t{cycle}z.pgrb2.{resolution}.f{forecast_hour}.grib2
```
Example: `gfs.t00z.pgrb2.0p25.f000.grib2`

### Metadata Files
```
{model}.t{cycle}z.pgrb2.{resolution}.f{forecast_hour}.json
```
Contains:
- Download timestamp
- File checksum
- Source URL
- Variable list
- Validation status

### Processed Data Files
```
{variable}_{grid}_{date}_{cycle}.{format}
```
Example: `temperature_h3_20250205_00z.parquet`

## Storage Implementation

### Local Filesystem Structure
```python
class ImmutableStorage:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.raw_path = base_path / "raw"
        self.processed_path = base_path / "processed"
        self.metadata_path = base_path / "metadata"
        
    def store_raw(self, source: str, date: date, cycle: str, 
                  filename: str, data: bytes) -> Path:
        """Store raw data with immutability guarantees"""
        # Construct path
        file_path = (self.raw_path / source / date.isoformat() / 
                    f"{cycle}z" / filename)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file already exists (immutable!)
        if file_path.exists():
            raise FileExistsError(f"File already exists: {file_path}")
        
        # Write data
        file_path.write_bytes(data)
        
        # Calculate and store checksum
        checksum = self._calculate_checksum(data)
        self._store_metadata(file_path, checksum)
        
        return file_path
```

### Metadata Schema
```json
{
  "file_id": "gfs_20250205_00z_f000_0p25",
  "source": "gfs",
  "date": "2025-02-05",
  "cycle": "00",
  "forecast_hour": 0,
  "resolution": "0.25",
  "filename": "gfs.t00z.pgrb2.0p25.f000.grib2",
  "file_size": 184567890,
  "checksum_sha256": "abc123...",
  "checksum_md5": "def456...",
  "download_timestamp": "2025-02-05T04:30:15Z",
  "download_url": "https://nomads.ncep.noaa.gov/...",
  "variables": ["2m_temperature", "surface_pressure"],
  "validation_status": "valid",
  "validation_timestamp": "2025-02-05T04:31:00Z",
  "storage_tier": "hot",
  "retention_days": 30
}
```

## Data Lifecycle Management

### Storage Tiers
| Tier | Access Pattern | Storage Medium | Retention | Cost |
|------|---------------|----------------|-----------|------|
| Hot | Frequent reads | SSD/NVMe | 7 days | High |
| Warm | Occasional reads | HDD | 30 days | Medium |
| Cold | Rare reads | Object Storage | 1 year | Low |
| Archive | Almost never | Tape/Glacier | 7 years | Very Low |

### Lifecycle Transitions
```
Ingestion → Hot (7 days) → Warm (30 days) → Cold (1 year) → Archive (7 years)
```

### Automated Transitions
```python
def manage_lifecycle():
    """Move data between storage tiers based on age"""
    for file_path in find_old_files("hot", days=7):
        move_to_tier(file_path, "warm")
    
    for file_path in find_old_files("warm", days=30):
        move_to_tier(file_path, "cold")
```

## Backup and Recovery

### Backup Strategy
1. **Incremental backups**: Daily for hot/warm storage
2. **Full backups**: Weekly for all tiers
3. **Geographic redundancy**: Cross-region replication for critical data
4. **Versioned backups**: Keep multiple versions of metadata

### Recovery Procedures
1. **File-level recovery**: Restore individual corrupted files from backups
2. **Dataset recovery**: Restore entire date/cycle from backups
3. **Disaster recovery**: Full restoration from off-site backups

## Capacity Planning

### Storage Requirements Estimate

#### GFS Data (0.25° resolution)
- Single forecast hour: ~180 MB
- Daily (4 cycles × 49 hours 0-48): ~35 GB
- 30-day retention: ~1 TB
- 1-year retention: ~12 TB

#### HRRR Data (CONUS, 3km)
- Single forecast hour: ~50 MB
- Daily (24 cycles × 18 hours): ~21 GB
- 30-day retention: ~630 GB

#### Observations (METAR/ASOS)
- Daily: ~100 MB
- 1-year retention: ~36 GB

#### Total Requirements (First Year)
- Hot storage (7 days): ~400 GB
- Warm storage (30 days): ~1.7 TB  
- Cold storage (1 year): ~13 TB
- Metadata: Negligible (< 10 GB)

### Growth Projections
- Year 1: 15 TB total
- Year 2: 30 TB (adding ECMWF, additional variables)
- Year 3: 50 TB (higher resolution, more frequent cycles)

## Performance Considerations

### Read/Write Patterns
- **Write**: Bursty (after model runs), sequential large files
- **Read**: Random access for specific variables/dates
- **Metadata**: Frequent small reads

### Optimization Strategies
1. **File grouping**: Store related forecast hours together
2. **Columnar storage**: Use Parquet for processed data
3. **Compression**: GZIP for NetCDF, Snappy for Parquet
4. **Indexing**: Spatial and temporal indexes for fast queries

## Security and Access Control

### Data Protection
1. **Encryption at rest**: AES-256 for all stored data
2. **Encryption in transit**: TLS 1.3 for all transfers
3. **Access logging**: Audit all data access
4. **Data integrity**: Regular checksum verification

### Access Policies
- **Raw data**: Read-only for all users
- **Processed data**: Read/write for processing jobs
- **Metadata**: Read-only for users, read/write for system
- **Backups**: Write-only for backup jobs, read-only for recovery

## Monitoring and Alerting

### Key Metrics
1. **Storage utilization**: Alert at 80%, 90%, 95% capacity
2. **Ingestion rate**: Monitor MB/sec, files/day
3. **Data integrity**: Checksum validation failures
4. **Access patterns**: Hot/cold data ratios

### Alerting Rules
- Storage capacity > 90%
- Ingestion failure rate > 5%
- Checksum mismatch detected
- Backup job failure

## Implementation Roadmap

### Phase 1 (Current)
- Local filesystem storage
- Basic immutability checks
- 30-day retention policy
- Manual backup procedures

### Phase 2 (Next 3 months)
- Object storage integration (S3 compatible)
- Automated lifecycle management
- Incremental backups
- Basic monitoring

### Phase 3 (Next 6 months)
- Multi-tier storage (hot/warm/cold)
- Geographic redundancy
- Advanced compression
- Performance optimization

### Phase 4 (Next 12 months)
- Data lake architecture
- Query optimization
- Cost optimization
- Advanced security features