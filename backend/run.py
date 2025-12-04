"""Production server runner for Railway deployment."""
import os
import sys

print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"PORT env: {os.environ.get('PORT', 'not set')}")
print("Starting server...")
sys.stdout.flush()

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting uvicorn on port {port}")
    sys.stdout.flush()
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)

