#!/usr/bin/env python3
"""
Simple HTTP server for OneWeather dashboard
For testing only - will be integrated into 1news.co
"""

import http.server
import socketserver
import os
import webbrowser
from datetime import datetime

PORT = 8081
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def log_message(self, format, *args):
        # Custom log format with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {self.address_string()} - {format % args}")
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def main():
    os.chdir(DIRECTORY)
    
    print("=" * 60)
    print("OneWeather Dashboard Server")
    print("=" * 60)
    print(f"Serving from: {DIRECTORY}")
    print(f"Dashboard URL: http://localhost:{PORT}")
    print(f"Demo location: Ardmore, PA (40.0048, -75.2923)")
    print("\nFeatures:")
    print("  • Apple/Tesla-style dark theme")
    print("  • Dark Sky-inspired hourly scroll")
    print("  • Mock data (awaiting API integration)")
    print("  • Responsive design")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
            # Try to open browser automatically
            try:
                webbrowser.open(f"http://localhost:{PORT}")
            except:
                pass
                
            print(f"\nServer started at http://localhost:{PORT}")
            print("Serving dashboard...")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"\nPort {PORT} is already in use.")
            print("Try: kill $(lsof -t -i:{PORT})")
        else:
            raise

if __name__ == "__main__":
    main()