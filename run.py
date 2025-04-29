import uvicorn
import logging
import sys
import os
import socket
import webbrowser
import time
import threading

# Set up logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Add file handler for persistent logging
try:
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
except Exception as e:
    logger.warning(f"Could not set up file logging: {e}")

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except socket.error:
            return True

def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    port = start_port
    while port < start_port + max_attempts:
        if not is_port_in_use(port):
            return port
        port += 1
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

def open_browser(port: int):
    """Open the browser after a short delay to allow the server to start"""
    time.sleep(2)  # Wait for server to start
    url = f"http://127.0.0.1:{port}"
    logger.info(f"Opening browser at {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    try:
        logger.info("Starting Ingreedy application...")
        
        # Check if required directories exist
        required_dirs = [
            'app/static',
            'app/templates',
            'app/data'
        ]
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                logger.error(f"Required directory not found: {dir_path}")
                sys.exit(1)
        
        # Find an available port
        try:
            port = find_available_port()
            logger.info(f"Using port {port}")
        except Exception as e:
            logger.error(f"Could not find available port: {e}")
            sys.exit(1)
        
        # Start browser in a separate thread
        browser_thread = threading.Thread(target=open_browser, args=(port,))
        browser_thread.daemon = True
        browser_thread.start()
        
        # Run the application
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=port,
            reload=True,
            log_level="debug",
            log_config=None  # Disable uvicorn's logging config to keep ours
        )
    except KeyboardInterrupt:
        logger.info("Shutting down application...")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        raise 