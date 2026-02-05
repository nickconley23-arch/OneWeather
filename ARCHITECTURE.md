# OneWeather System Architecture

## Overview
OneWeather is an accuracy-first weather intelligence platform that blends multiple forecast sources using machine learning to provide superior accuracy. This document describes the system architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   1news.co      │  │   iOS Mobile    │                   │
│  │  Integration    │  │     App         │                   │
│  │  (Dark Sky-like)│  │  (SwiftUI)      │                   │
│  └─────────────────┘  └─────────────────┘                   │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │  Public API     │  │  Admin Dashboard│                   │
│  │  Consumers      │  │  (Internal)     │                   │
│  └─────────────────┘  └─────────────────┘                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS/JSON
┌──────────────────────────▼──────────────────────────────────┐
│                    API Gateway Layer                         │
│  • FastAPI Application                                      │
│  • Authentication & Rate Limiting                           │
│  • Request Routing & Validation                             │
│  • Response Caching (Redis)                                 │
│  • Mobile-optimized endpoints                               │
│  • Web-optimized endpoints                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │ Internal API Calls
┌──────────────────────────▼──────────────────────────────────┐
│                  Core Service Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Forecast   │  │ Evaluation │  │ ML Service │            │
│  │ Service    │  │ Service    │  │            │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└──────────────────────────┬──────────────────────────────────┘
                           │ Database/Storage Access
┌──────────────────────────▼──────────────────────────────────┐
│                  Data & Storage Layer                        │
│  • TimescaleDB (Processed forecasts, evaluations)           │
│  • Object Storage (Raw GRIB/NetCDF files)                   │
│  • Redis Cache (Frequent queries, session data)             │
└──────────────────────────┬──────────────────────────────────┘
                           │ Data Pipeline
┌──────────────────────────▼──────────────────────────────────┐
│                Data Processing Pipeline                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Ingestion  │  │Normalization│  │Evaluation  │            │
│  │ Pipeline   │  │  Pipeline   │  │  Pipeline  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└──────────────────────────┬──────────────────────────────────┘
                           │ External APIs
┌──────────────────────────▼──────────────────────────────────┐
│                  External Data Sources                       │
│  • NOAA/NCEP (GFS, HRRR, NAM)                              │
│  • METAR/ASOS Observations                                 │
│  • Future: ECMWF, CMC, JMA                                 │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Ingestion Pipeline

#### Connectors
- **GFS Connector**: Downloads 0.25° resolution forecasts from NOMADS
- **HRRR Connector**: Downloads 3km CONUS forecasts
- **NAM Connector**: Downloads 12km CONUS forecasts  
- **METAR Connector**: Fetches surface observations

#### Storage Strategy
```
data/
├── raw/                      # Immutable raw data
│   ├── gfs/
│   │   ├── 2025-02-05/
│   │   │   ├── 00z/
│   │   │   │   ├── gfs.t00z.pgrb2.0p25.f000
│   │   │   │   └── metadata.json
│   │   │   └── 12z/
│   ├── hrrr/
│   ├── nam/
│   └── observations/
├── processed/                # Normalized H3-gridded data
│   ├── gfs/
│   │   ├── 2025-02-05/
│   │   │   └── 00z_h3.parquet
│   ├── hrrr/
│   └── nam/
└── evaluations/              # Accuracy assessments
    ├── daily/
    └── monthly/
```

#### H3 Spatial Grid
- **Resolution**: H3 resolution 6 (~3.7km² cells)
- **Coverage**: CONUS initially (H3 cells covering 24°N-50°N, 125°W-66°W)
- **Benefits**: Uniform cell size, fast spatial queries, hierarchical indexing

### 2. Normalization Pipeline

#### Process Flow
```
Raw GRIB/NetCDF → Variable Extraction → Regridding → H3 Format → Parquet Storage
```

#### Key Operations:
1. **Variable Extraction**: Extract 2m temperature from GRIB files
2. **Regridding**: Bilinear interpolation from source grid to H3 cells
3. **Temporal Alignment**: Interpolate to standard forecast hours (0, 1, 3, 6, 12, 24, 48)
4. **Quality Control**: Validate data ranges, handle missing values

### 3. Evaluation Engine

#### Metrics Calculated:
- **Mean Absolute Error (MAE)**: per H3 cell, per forecast hour
- **Root Mean Square Error (RMSE)**: per H3 cell, per forecast hour
- **Bias**: Systematic over/under prediction
- **Skill Score**: Relative to climatology or persistence

#### Evaluation Process:
```
Observations → Spatial Matching → Temporal Alignment → Metric Calculation → Storage
```

### 4. Machine Learning Service (Phase 2)

#### Models:
1. **Source Selection Classifier**: Predicts best source per (location, horizon, season)
2. **Blending Regressor**: Optimal weights for combining multiple sources
3. **Bias Correction**: Post-processing to reduce systematic errors

#### Features:
- Geographic features (latitude, longitude, elevation, distance to coast)
- Temporal features (hour of day, day of year, forecast horizon)
- Weather regime features (temperature, pressure patterns)
- Historical performance features

### 5. API Service (FastAPI)

#### Endpoints:
```
GET  /api/v1/forecast/{latitude}/{longitude}
GET  /api/v1/forecast/{h3_index}
GET  /api/v1/sources/{source}/performance
GET  /api/v1/evaluations/{date}/{metric}
POST /api/v1/admin/ingestion/trigger
```

#### Response Format:
```json
{
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "h3_index": "862a1072fffffff"
  },
  "forecast": {
    "source": "blended",
    "timestamp": "2025-02-05T00:00:00Z",
    "values": [
      {
        "forecast_hour": 0,
        "temperature_c": 5.2,
        "confidence": 0.85,
        "sources": ["gfs", "hrrr"]
      }
    ]
  },
  "metadata": {
    "generated_at": "2025-02-05T04:30:00Z",
    "cache_hit": true
  }
}
```

### 6. Storage Layer

#### TimescaleDB Schema:
```sql
-- Processed forecasts
CREATE TABLE forecasts (
    time TIMESTAMPTZ NOT NULL,
    h3_index TEXT NOT NULL,
    source TEXT NOT NULL,
    forecast_hour INTEGER NOT NULL,
    temperature_c DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Observations
CREATE TABLE observations (
    time TIMESTAMPTZ NOT NULL,
    station_id TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    temperature_c DOUBLE PRECISION
);

-- Evaluations
CREATE TABLE evaluations (
    evaluation_date DATE NOT NULL,
    h3_index TEXT NOT NULL,
    source TEXT NOT NULL,
    forecast_hour INTEGER NOT NULL,
    mae DOUBLE PRECISION,
    rmse DOUBLE PRECISION,
    bias DOUBLE PRECISION
);

-- Create hypertables for time-series data
SELECT create_hypertable('forecasts', 'time');
SELECT create_hypertable('observations', 'time');
```

#### Object Storage:
- **Raw files**: GRIB2, NetCDF (immutable, versioned)
- **Processed files**: Parquet (H3-gridded, compressed)
- **Backup**: Daily snapshots, 14-day retention

### 7. Infrastructure

#### Development Environment:
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: ./api
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/oneweather
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: timescale/timescaledb:latest-pg14
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=oneweather
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
  
  ingestion:
    build: ./ingestion
    volumes:
      - ./data:/data
  
  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
  
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]

volumes:
  postgres_data:
```

#### Production Deployment (Railway/Vercel):
- **API**: FastAPI container with auto-scaling
- **Database**: TimescaleDB managed service
- **Storage**: S3-compatible object storage
- **Cache**: Redis Cloud
- **Monitoring**: Built-in + custom Prometheus

#### Future AWS Migration:
- **ECS/EKS**: Container orchestration
- **RDS**: Managed PostgreSQL with TimescaleDB extension
- **S3**: Object storage with lifecycle policies
- **ElastiCache**: Redis managed service
- **CloudWatch**: Monitoring and alerting

## Data Flow

### Real-time Forecast Request:
```
1. Client → API Gateway → Forecast Service
2. Forecast Service → Cache Check (Redis)
3. Cache Miss → Database Query (TimescaleDB)
4. Database → Return Forecast → Cache Population
5. Forecast Service → Response to Client
```

### Data Ingestion Pipeline:
```
1. Scheduler → Trigger Connector
2. Connector → Download from NOAA → Raw Storage
3. Normalization → Regrid to H3 → Processed Storage
4. Evaluation → Compare with Observations → Metrics Storage
5. ML Service → Update Models (Periodically)
```

## Security Architecture

### Authentication & Authorization:
- **API Keys**: For external consumers
- **JWT Tokens**: For admin users
- **Role-Based Access Control**: Admin vs Read-only

### Data Protection:
- **Encryption at Rest**: AES-256 for sensitive data
- **Encryption in Transit**: TLS 1.3 for all communications
- **Secrets Management**: Environment variables + secret manager

### Network Security:
- **VPC Isolation**: Private subnets for databases
- **Security Groups**: Minimal required access
- **WAF**: Web Application Firewall for API

## Monitoring & Observability

### Metrics Collected:
- **API**: Request rate, latency, error rate, cache hit rate
- **Database**: Query performance, connection count, storage usage
- **Ingestion**: Download success rate, processing time, data latency
- **System**: CPU, memory, disk, network usage

### Alerting Rules:
- **Critical**: API down, database unavailable, ingestion failing
- **Warning**: High latency, low cache hit rate, disk space low
- **Info**: New model deployed, data source added

### Dashboards:
1. **System Health**: Overall status and key metrics
2. **API Performance**: Request patterns and response times
3. **Data Pipeline**: Ingestion status and data quality
4. **Forecast Accuracy**: Model performance over time

## Scalability Considerations

### Horizontal Scaling:
- **API Layer**: Stateless, auto-scaling based on CPU/memory
- **Ingestion**: Multiple workers for different data sources
- **Processing**: Batch processing with parallel workers

### Database Scaling:
- **Read Replicas**: For analytical queries
- **Connection Pooling**: PgBouncer for connection management
- **Query Optimization**: Indexes on time and h3_index

### Cache Strategy:
- **L1 Cache**: In-memory (Redis) for frequent queries
- **L2 Cache**: CDN for static assets and common requests
- **Cache Invalidation**: Time-based + event-based

## Disaster Recovery

### Backup Strategy:
- **Database**: Daily snapshots + WAL archiving
- **Raw Data**: Immutable storage with versioning
- **Configuration**: Version-controlled in Git

### Recovery Procedures:
- **Database Failure**: Restore from snapshot + WAL replay
- **API Failure**: Auto-scaling + health checks
- **Data Corruption**: Re-ingest from raw immutable storage

### High Availability:
- **Multi-AZ Deployment**: For critical components
- **Load Balancing**: Across multiple availability zones
- **Health Checks**: Automatic failover for unhealthy instances

## Development Workflow

### Git Strategy:
- **Main Branch**: Production-ready code
- **Feature Branches**: Short-lived, PR-based development
- **Release Tags**: Semantic versioning (v1.0.0)

### CI/CD Pipeline:
```
Code Push → Lint/Test → Build Image → Deploy Staging → Tests → Deploy Production
```

### Testing Strategy:
- **Unit Tests**: Isolated component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Full pipeline testing
- **Performance Tests**: Load and stress testing

---

*Architecture Version: 1.0*
*Last Updated: 2026-02-05*
*Maintainer: Claw Senior Dev*