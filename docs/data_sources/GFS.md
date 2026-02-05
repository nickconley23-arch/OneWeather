# GFS (Global Forecast System) Data Source Documentation

## Overview
The Global Forecast System (GFS) is a weather forecast model produced by the National Centers for Environmental Prediction (NCEP). It provides global weather forecasts up to 16 days ahead (384 hours).

## Data Access Methods

### Primary Sources
1. **NOMADS Server (NOAA Operational Model Archive and Distribution System)**
   - HTTPS: `https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/`
   - FTP: `ftp://ftp.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/`

2. **NCEP FTP/HTTP Server**
   - Provides the same data as NOMADS

### File Naming Convention
```
gfs.tCCz.pgrb2.RES.fFFF
```
Where:
- `CC` = Model cycle runtime (00, 06, 12, 18 UTC)
- `RES` = Resolution (0p25, 0p50, 1p00)
- `FFF` = Forecast hour (000-384)
- Example: `gfs.t00z.pgrb2.0p25.f000` = 00Z run, 0.25° resolution, analysis time

## Available Data Products

### Primary GRIB2 Products (Most Commonly Used)

| Resolution | File Pattern | Grid Size | Description |
|------------|--------------|-----------|-------------|
| 0.25° | `gfs.tCCz.pgrb2.0p25.fFFF` | 1440×721 | High resolution global grid |
| 0.50° | `gfs.tCCz.pgrb2.0p50.fFFF` | 720×361 | Medium resolution global grid |
| 1.00° | `gfs.tCCz.pgrb2.1p00.fFFF` | 360×181 | Low resolution global grid |

### Secondary GRIB2 Products (Less Common Parameters)
- `gfs.tCCz.pgrb2b.RES.fFFF` - Additional parameters not in primary files
- `gfs.tCCz.pgrb2full.0p50.fFFF` - Combined primary and secondary parameters (0.5° only)

### Other Formats
- **NetCDF**: `gfs.tCCz.atmfFFF.nc` (atmospheric), `gfs.tCCz.sfcfFFF.nc` (surface)
- **BUFR**: Observation data and quality-controlled prepbufr files
- **Text**: Tropical cyclone vital statistics, satellite bias corrections

## Temporal Characteristics

### Model Cycles
- **Run times**: 00Z, 06Z, 12Z, 18Z (4 times daily)
- **Forecast length**: 384 hours (16 days)
- **Output frequency**: Varies by forecast hour:
  - Hours 0-120: 1-hour intervals
  - Hours 120-240: 3-hour intervals  
  - Hours 240-384: 12-hour intervals

### Update Schedule
- Initialization completes approximately 4-5 hours after model run time
- Full forecast available ~6 hours after run time
- Data retention: Typically 10-14 days on operational servers

## Spatial Coverage and Resolution

### Global Coverage
- Latitude: 90°N to 90°S
- Longitude: 0°E to 359.75°E (0.25° resolution)

### Grid Types
1. **Regular Latitude-Longitude Grid** (pgrb2 files)
   - Uniform spacing in degrees
   - Most common for applications

2. **Reduced Gaussian Grid** (sfluxgrb files)
   - Variable resolution with higher density at poles
   - Used for spectral model output

## Key Meteorological Variables

### Surface/2m Variables (Essential for Temperature Forecasting)
- **2m Temperature** (`TMP:2 m above ground`)
- **2m Dew Point Temperature** (`DPT:2 m above ground`)
- **Surface Pressure** (`PRES:surface`)
- **10m Wind Components** (`UGRD:10 m above ground`, `VGRD:10 m above ground`)
- **Precipitation** (`APCP:surface`)
- **Cloud Cover** (`TCDC:entire atmosphere`)
- **Relative Humidity** (`RH:2 m above ground`)

### Upper Air Variables
- Temperature, geopotential height, wind at pressure levels (1000, 850, 700, 500, 250 hPa, etc.)
- Vertical velocity, specific humidity

### Derived/Diagnostic Variables
- **Heat Index**, **Wind Chill**
- **Precipitable Water**
- **CAPE** (Convective Available Potential Energy)

## Data Format: GRIB2

### GRIB2 Structure
- Binary format with efficient compression
- Contains multiple messages (parameters/levels) per file
- Each message has metadata and data section
- Uses WMO standard GRIB edition 2

### Tools for Working with GRIB2
1. **wgrib2** - Command-line utility for inspection and processing
2. **cfgrib** - Python interface via xarray/ecCodes
3. **pygrib** - Python bindings to ecCodes
4. **NCL** (NCAR Command Language) - Meteorological data analysis

## Storage Considerations

### File Sizes (Approximate)
| Resolution | Single Forecast Hour | Full Forecast (384h) |
|------------|---------------------|----------------------|
| 0.25° | ~180 MB | ~70 GB |
| 0.50° | ~45 MB | ~17 GB |
| 1.00° | ~11 MB | ~4 GB |

### Compression
- GRIB2 uses JPEG2000 or simple packing compression
- Typical compression ratio: 3:1 to 10:1
- NetCDF files can be further compressed with gzip

## Access Patterns for OneWeather

### Recommended Configuration
1. **Resolution**: 0.25° for CONUS-focused analysis
2. **Variables**: Subset to essential surface/2m parameters
3. **Forecast Range**: 0-48 hours for initial phase
4. **Update Frequency**: Download each cycle (4× daily)

### Efficient Download Strategy
- Use HTTP range requests for partial file downloads
- Consider CDSAPI or AWS S3 access for bulk historical data
- Implement retry logic with exponential backoff

## Quality and Limitations

### Known Issues
1. **Cold bias** in surface temperatures, especially at night
2. **Underestimation** of precipitation intensity
3. **Smooth topography** representation affects local conditions
4. **Model drift** beyond 5-7 days reduces skill

### Verification Sources
- MADIS (Meteorological Assimilation Data Ingest System)
- NCEP/EMC verification statistics
- Local ASOS/METAR observations for ground truth

## References and Links

### Official Documentation
- [NCEP GFS Product Description](https://www.nco.ncep.noaa.gov/pmb/products/gfs/)
- [NOMADS Data Access](https://nomads.ncep.noaa.gov/)
- [GFS Technical Implementation](https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs.php)

### Community Resources
- [Unidata GFS Tutorial](https://unidata.github.io/MetPy/latest/tutorials/GFS_ingest.html)
- [ECMWF GRIB API](https://confluence.ecmwf.int/display/ECC)
- [Weather.gov GFS Page](https://www.weather.gov/mdl/gfs_home)

### Data Access Tools
- [wgrib2 Documentation](https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/)
- [cfgrib Python Package](https://github.com/ecmwf/cfgrib)
- [Herbie: Smart GFS Downloader](https://github.com/blaylockbk/Herbie)