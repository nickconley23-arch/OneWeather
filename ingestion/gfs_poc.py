#!/usr/bin/env python3
"""
GFS Data Ingestion Proof-of-Concept

This script demonstrates downloading and inspecting a single GFS forecast file
from the NOMADS server. It implements the core functionality needed for the
OneWeather ingestion pipeline.

Features:
1. Downloads a GFS forecast file (0.25° resolution, analysis time)
2. Validates the download with checksum
3. Extracts basic metadata from the GRIB2 file
4. Stores data in immutable raw format with metadata
5. Provides example of how to parse GRIB2 data

Requirements:
- wgrib2 command-line tool (for GRIB2 inspection)
- requests library (for HTTP downloads)
- Optional: cfgrib for Python GRIB2 parsing

Usage:
    python gfs_poc.py --cycle 00 --date 2025-02-05 --forecast-hour 0
"""

import os
import sys
import json
import hashlib
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import subprocess
import time

# Third-party imports (install with pip install requests)
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Error: requests library not installed. Run: pip install requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GFSIngestor:
    """GFS data ingestion proof-of-concept"""
    
    def __init__(self, base_dir: str = "/home/ubuntu/OneWeather/data"):
        """
        Initialize the GFS ingestor
        
        Args:
            base_dir: Base directory for data storage
        """
        self.base_dir = Path(base_dir)
        self.raw_dir = self.base_dir / "raw" / "gfs"
        self.metadata_dir = self.base_dir / "metadata" / "gfs"
        
        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # GFS data source configuration
        self.base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod"
        
        # Configure HTTP session with retry logic
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'User-Agent': 'OneWeather/1.0 (https://github.com/yourusername/oneweather)'
        })
        return session
    
    def construct_url(self, date: str, cycle: str, forecast_hour: int = 0, 
                     resolution: str = "0p25") -> str:
        """
        Construct the URL for a GFS forecast file
        
        Args:
            date: Date in YYYYMMDD format
            cycle: Model cycle (00, 06, 12, 18)
            forecast_hour: Forecast hour (0-384)
            resolution: Grid resolution (0p25, 0p50, 1p00)
            
        Returns:
            Complete URL to download
        """
        # Format forecast hour as 3-digit string
        fhour = f"{forecast_hour:03d}"
        
        # Construct filename
        filename = f"gfs.t{cycle}z.pgrb2.{resolution}.f{fhour}"
        
        # Construct URL path
        url = f"{self.base_url}/gfs.{date}/{cycle}/atmos/{filename}"
        
        return url
    
    def download_file(self, url: str, output_path: Path) -> bool:
        """
        Download a file with progress tracking and validation
        
        Args:
            url: URL to download
            output_path: Path to save the file
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            logger.info(f"Downloading {url}")
            
            # Stream the download to handle large files
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get file size for progress tracking
            total_size = int(response.headers.get('content-length', 0))
            
            # Download with progress
            downloaded = 0
            start_time = time.time()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress every 10MB
                        if downloaded % (10 * 1024 * 1024) < 8192:
                            elapsed = time.time() - start_time
                            speed = downloaded / elapsed / 1024 / 1024  # MB/s
                            logger.info(f"Downloaded {downloaded/1024/1024:.1f}MB "
                                      f"({speed:.1f} MB/s)")
            
            elapsed = time.time() - start_time
            logger.info(f"Download complete: {output_path.name} "
                       f"({downloaded/1024/1024:.1f}MB in {elapsed:.1f}s)")
            
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return False
    
    def calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA256 checksum of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 checksum as hex string
        """
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def extract_grib_metadata(self, grib_path: Path) -> Dict:
        """
        Extract basic metadata from GRIB2 file using wgrib2
        
        Args:
            grib_path: Path to GRIB2 file
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            "file_size": grib_path.stat().st_size,
            "variables": [],
            "levels": [],
            "grid_info": {}
        }
        
        try:
            # Use wgrib2 to inspect the file
            # First, get inventory of messages
            cmd = ["wgrib2", str(grib_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                metadata["message_count"] = len(lines)
                
                # Extract unique variables and levels
                variables = set()
                levels = set()
                
                for line in lines:
                    # Parse wgrib2 output format
                    parts = line.split(':')
                    if len(parts) > 3:
                        var_info = parts[3]
                        # Extract variable name (simplified)
                        if ':' in var_info:
                            var_name = var_info.split(':')[0]
                            variables.add(var_name)
                        
                        # Extract level information
                        if len(parts) > 4:
                            level_info = parts[4]
                            levels.add(level_info)
                
                metadata["variables"] = sorted(list(variables))
                metadata["levels"] = sorted(list(levels))
                
                # Get grid information
                cmd_grid = ["wgrib2", str(grib_path), "-grid"]
                result_grid = subprocess.run(cmd_grid, capture_output=True, text=True)
                
                if result_grid.returncode == 0 and result_grid.stdout:
                    # Parse grid information
                    grid_lines = result_grid.stdout.strip().split('\n')
                    if grid_lines:
                        metadata["grid_info"] = {"description": grid_lines[0]}
            
            else:
                logger.warning(f"wgrib2 failed: {result.stderr}")
                
        except FileNotFoundError:
            logger.warning("wgrib2 not found in PATH. Install with: "
                          "apt-get install wgrib2 or conda install -c conda-forge wgrib2")
        except Exception as e:
            logger.warning(f"Error extracting GRIB metadata: {e}")
        
        return metadata
    
    def ingest_forecast(self, date: str, cycle: str, forecast_hour: int = 0,
                       resolution: str = "0p25") -> Tuple[bool, Dict]:
        """
        Ingest a single GFS forecast file
        
        Args:
            date: Date in YYYYMMDD format
            cycle: Model cycle (00, 06, 12, 18)
            forecast_hour: Forecast hour (0-384)
            resolution: Grid resolution
            
        Returns:
            Tuple of (success, metadata)
        """
        # Construct paths
        date_dir = self.raw_dir / date / f"{cycle}z"
        date_dir.mkdir(parents=True, exist_ok=True)
        
        fhour = f"{forecast_hour:03d}"
        filename = f"gfs.t{cycle}z.pgrb2.{resolution}.f{fhour}"
        file_path = date_dir / filename
        
        metadata_path = self.metadata_dir / date / f"{cycle}z" / f"{filename}.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file already exists
        if file_path.exists():
            logger.info(f"File already exists: {file_path}")
            
            # Load existing metadata
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                return True, metadata
            else:
                # Extract metadata from existing file
                metadata = self.extract_grib_metadata(file_path)
                return True, metadata
        
        # Construct URL
        url = self.construct_url(date, cycle, forecast_hour, resolution)
        
        # Download file
        success = self.download_file(url, file_path)
        
        if not success:
            return False, {}
        
        # Calculate checksum
        checksum = self.calculate_checksum(file_path)
        
        # Extract metadata
        grib_metadata = self.extract_grib_metadata(file_path)
        
        # Create comprehensive metadata
        metadata = {
            "source": "gfs",
            "date": date,
            "cycle": cycle,
            "forecast_hour": forecast_hour,
            "resolution": resolution,
            "filename": filename,
            "download_time": datetime.utcnow().isoformat() + "Z",
            "file_size": file_path.stat().st_size,
            "checksum_sha256": checksum,
            "url": url,
            "grib_metadata": grib_metadata,
            "status": "ingested"
        }
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Ingestion complete: {filename}")
        logger.info(f"  Size: {metadata['file_size'] / 1024 / 1024:.1f}MB")
        logger.info(f"  Variables: {len(grib_metadata.get('variables', []))}")
        
        return True, metadata
    
    def list_available_cycles(self, date: str = None) -> Dict:
        """
        List available GFS cycles for a given date
        
        Args:
            date: Date in YYYYMMDD format (default: today)
            
        Returns:
            Dictionary of available cycles and their status
        """
        if date is None:
            date = datetime.utcnow().strftime("%Y%m%d")
        
        cycles = {}
        available_cycles = ["00", "06", "12", "18"]
        
        for cycle in available_cycles:
            # Check if cycle directory exists on server
            url = f"{self.base_url}/gfs.{date}/{cycle}/"
            
            try:
                response = self.session.head(url, timeout=10)
                exists = response.status_code == 200
            except:
                exists = False
            
            # Check if we have data locally
            local_dir = self.raw_dir / date / f"{cycle}z"
            local_exists = local_dir.exists() and any(local_dir.iterdir())
            
            cycles[cycle] = {
                "available_on_server": exists,
                "available_locally": local_exists,
                "url": url
            }
        
        return cycles

def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description="GFS Data Ingestion Proof-of-Concept")
    parser.add_argument("--date", type=str, default=None,
                       help="Date in YYYYMMDD format (default: today)")
    parser.add_argument("--cycle", type=str, default="00",
                       choices=["00", "06", "12", "18"],
                       help="Model cycle (default: 00)")
    parser.add_argument("--forecast-hour", type=int, default=0,
                       help="Forecast hour (default: 0, analysis)")
    parser.add_argument("--resolution", type=str, default="0p25",
                       choices=["0p25", "0p50", "1p00"],
                       help="Grid resolution (default: 0p25)")
    parser.add_argument("--list-cycles", action="store_true",
                       help="List available cycles instead of downloading")
    parser.add_argument("--base-dir", type=str, 
                       default="/home/ubuntu/OneWeather/data",
                       help="Base directory for data storage")
    
    args = parser.parse_args()
    
    # Set default date to today if not provided
    if args.date is None:
        args.date = datetime.utcnow().strftime("%Y%m%d")
    
    # Initialize ingestor
    ingestor = GFSIngestor(base_dir=args.base_dir)
    
    if args.list_cycles:
        # List available cycles
        print(f"Checking available cycles for {args.date}...")
        cycles = ingestor.list_available_cycles(args.date)
        
        print(f"\nAvailable cycles for {args.date}:")
        print("-" * 60)
        for cycle, info in cycles.items():
            server_status = "✓" if info["available_on_server"] else "✗"
            local_status = "✓" if info["available_locally"] else "✗"
            print(f"Cycle {cycle}Z: Server: {server_status} | Local: {local_status}")
        
        return
    
    # Ingest specified forecast
    print(f"Ingesting GFS forecast:")
    print(f"  Date: {args.date}")
    print(f"  Cycle: {args.cycle}Z")
    print(f"  Forecast hour: {args.forecast_hour}")
    print(f"  Resolution: {args.resolution}°")
    print("-" * 60)
    
    success, metadata = ingestor.ingest_forecast(
        date=args.date,
        cycle=args.cycle,
        forecast_hour=args.forecast_hour,
        resolution=args.resolution
    )
    
    if success:
        print("\n✅ Ingestion successful!")
        print(f"\nMetadata summary:")
        print(f"  File: {metadata.get('filename')}")
        print(f"  Size: {metadata.get('file_size', 0) / 1024 / 1024:.1f} MB")
        print(f"  Variables found: {len(metadata.get('grib_metadata', {}).get('variables', []))}")
        print(f"  Checksum: {metadata.get('checksum_sha256', '')[:16]}...")
        print(f"  Stored at: {ingestor.raw_dir / args.date / f'{args.cycle}z'}")
    else:
        print("\n❌ Ingestion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()