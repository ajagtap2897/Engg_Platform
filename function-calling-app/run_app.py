#!/usr/bin/env python3
"""
OpenAI Function Calling Weather Assistant Launcher
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Launch the Function Calling Weather Assistant"""
    try:
        logger.info("🌤️ Starting OpenAI Function Calling Weather Assistant...")
        
        # Set working directory
        project_root = Path(__file__).parent.absolute()
        os.chdir(project_root)
        
        # Check for .env file
        env_file = project_root / ".env"
        if not env_file.exists():
            logger.warning("⚠️ .env file not found!")
            logger.info("💡 Please copy .env.example to .env and add your API keys")
        
        # Streamlit configuration
        streamlit_config = [
            "streamlit", "run", "src/app.py",
            "--server.port", "8504",
            "--server.address", "localhost",
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ]
        
        logger.info("🌐 Starting Streamlit server...")
        logger.info("📍 Application will be available at: http://localhost:8504")
        
        # Launch Streamlit
        subprocess.run(streamlit_config, check=True)
        
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()