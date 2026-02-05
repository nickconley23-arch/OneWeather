#!/usr/bin/env python3
"""
Test script for GFS ingestion proof-of-concept

This script tests the basic functionality of the GFS ingestor
without actually downloading large files.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gfs_poc import GFSIngestor

def test_url_construction():
    """Test URL construction logic"""
    ingestor = GFSIngestor(base_dir="/tmp/test")
    
    # Test basic URL construction
    url = ingestor.construct_url("20250205", "00", 0, "0p25")
    expected = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20250205/00/atmos/gfs.t00z.pgrb2.0p25.f000"
    assert url == expected, f"URL mismatch: {url}"
    
    # Test with different parameters
    url = ingestor.construct_url("20250205", "12", 24, "0p50")
    expected = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20250205/12/atmos/gfs.t12z.pgrb2.0p50.f024"
    assert url == expected, f"URL mismatch: {url}"
    
    print("✅ URL construction tests passed")

def test_directory_structure():
    """Test directory creation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        ingestor = GFSIngestor(base_dir=tmpdir)
        
        # Check that directories were created
        assert (Path(tmpdir) / "raw" / "gfs").exists()
        assert (Path(tmpdir) / "metadata" / "gfs").exists()
        
        print("✅ Directory structure tests passed")

def test_checksum_calculation():
    """Test checksum calculation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        ingestor = GFSIngestor(base_dir=tmpdir)
        
        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Calculate checksum
        checksum = ingestor.calculate_checksum(test_file)
        
        # Expected SHA256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert checksum == expected, f"Checksum mismatch: {checksum}"
        
        print("✅ Checksum calculation tests passed")

def test_metadata_storage():
    """Test metadata JSON storage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        ingestor = GFSIngestor(base_dir=tmpdir)
        
        # Create test metadata
        test_metadata = {
            "source": "gfs",
            "date": "20250205",
            "cycle": "00",
            "status": "test"
        }
        
        # Save metadata
        metadata_path = Path(tmpdir) / "metadata" / "gfs" / "test.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_path, 'w') as f:
            json.dump(test_metadata, f)
        
        # Load and verify
        with open(metadata_path, 'r') as f:
            loaded_metadata = json.load(f)
        
        assert loaded_metadata == test_metadata, "Metadata mismatch"
        
        print("✅ Metadata storage tests passed")

@patch('gfs_poc.requests.Session')
def test_download_mock(mock_session_class):
    """Test download functionality with mocked HTTP"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'content-length': '1000'}
    mock_response.iter_content.return_value = [b'test' * 250]  # 1000 bytes
    
    mock_session = Mock()
    mock_session.get.return_value = mock_response
    mock_session_class.return_value = mock_session
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ingestor = GFSIngestor(base_dir=tmpdir)
        ingestor.session = mock_session
        
        # Test download
        test_url = "https://example.com/test.grib2"
        output_path = Path(tmpdir) / "test.grib2"
        
        success = ingestor.download_file(test_url, output_path)
        
        assert success, "Download should succeed with mock"
        assert output_path.exists(), "Output file should exist"
        assert output_path.stat().st_size == 1000, "File size should match mock"
        
        print("✅ Mock download tests passed")

def test_list_cycles_mock():
    """Test cycle listing with mocked responses"""
    with tempfile.TemporaryDirectory() as tmpdir:
        ingestor = GFSIngestor(base_dir=tmpdir)
        
        # Mock the session's head method
        with patch.object(ingestor.session, 'head') as mock_head:
            # Simulate all cycles available
            mock_response = Mock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response
            
            cycles = ingestor.list_available_cycles("20250205")
            
            assert "00" in cycles
            assert "06" in cycles
            assert "12" in cycles
            assert "18" in cycles
            
            for cycle in cycles.values():
                assert cycle["available_on_server"] == True
                assert cycle["available_locally"] == False
            
            print("✅ Cycle listing tests passed")

def run_all_tests():
    """Run all tests"""
    print("Running GFS ingestion proof-of-concept tests...")
    print("=" * 60)
    
    tests = [
        test_url_construction,
        test_directory_structure,
        test_checksum_calculation,
        test_metadata_storage,
        test_download_mock,
        test_list_cycles_mock,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} failed: {e}")
    
    print("=" * 60)
    print(f"Test summary: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())