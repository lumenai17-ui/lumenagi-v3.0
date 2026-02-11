#!/usr/bin/env python3
"""
Test Result: SWARM Multi-Agent Flow
====================================

Task: "Create a simple Python HTTP server with basic auth"

Agent Routing (Kimi Coordinator):
- Analysis: Simple code generation → Route to Qwen 32B (local)
- No research needed → Skip GPT-4o
- No images → Skip Vision API

Agent: Qwen 32B (Local, ollama/qwen2.5:32b)
Speed: ~35 tok/s
Cost: $0
"""

import http.server
import socketserver
import base64
from functools import partial

PORT = 8000
USERNAME = "admin"
PASSWORD = "secret123"  # Change this!

class BasicAuthHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with basic authentication."""
    
    def __init__(self, *args, username=None, password=None, **kwargs):
        self.username = username
        self.password = password
        super().__init__(*args, **kwargs)
    
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
    
    def do_AUTHHEAD(self):
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="LumenAGI"')
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Authentication required")
    
    def do_GET(self):
        # Check authorization
        auth_header = self.headers.get("Authorization")
        
        if auth_header is None:
            self.do_AUTHHEAD()
            return
        
        # Parse basic auth
        try:
            auth_type, auth_string = auth_header.split(" ", 1)
            if auth_type.lower() != "basic":
                self.do_AUTHHEAD()
                return
            
            decoded = base64.b64decode(auth_string).decode("utf-8")
            user, pwd = decoded.split(":", 1)
            
            if user != self.username or pwd != self.password:
                self.do_AUTHHEAD()
                return
                
        except Exception:
            self.do_AUTHHEAD()
            return
        
        # Serve file
        super().do_GET()
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"[{self.log_date_time_string()}] {self.client_address[0]} - {format % args}")


def run_server(port=PORT, username=USERNAME, password=PASSWORD):
    """Run the authenticated HTTP server."""
    handler = partial(BasicAuthHandler, username=username, password=password)
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🚀 Server running on http://localhost:{port}/")
        print(f"👤 Username: {username}")
        print(f"🔑 Password: {'*' * len(password)}")
        print("Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")


if __name__ == "__main__":
    run_server()

# Test with:
# curl -u admin:secret123 http://localhost:8000/
