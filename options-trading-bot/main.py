#!/usr/bin/env python3
"""Main entry point for the options trading bot"""

import sys
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=True
    )
