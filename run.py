import os
import uvicorn
import webbrowser
import threading
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=".env")

# Check for required environment variables
if not os.getenv("SPOONACULAR_API_KEY"):
    print("WARNING: SPOONACULAR_API_KEY is not set in your .env file.")
    print("You will need an API key from https://spoonacular.com/food-api to use external recipe data.")
    print("The application will still run with limited functionality using local data only.")
    print("Create a .env file with SPOONACULAR_API_KEY=your_api_key to enable full functionality.")
    print()

def open_browser(port):
    """Open browser after a short delay to ensure server is up"""
    time.sleep(2)
    webbrowser.open(f"http://localhost:{port}")
    print(f"Browser opened to http://localhost:{port}")

# Run the application
if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Start a thread to open the browser after server starts
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    
    print(f"Starting Ingreedy Recipe Chatbot...")
    print(f"Opening your browser to http://localhost:{port} in a moment...")
    
    # Start the server
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 