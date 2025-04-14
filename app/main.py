from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from dotenv import load_dotenv
import os
import logging

from app.api.recipe_service import RecipeService
from app.ml.recipe_recommender import RecipeRecommender

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Ingreedy - Recipe Chatbot")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Initialize services
recipe_service = RecipeService()
recipe_recommender = RecipeRecommender(recipe_service)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page"""
    try:
        # Get some initial recipes to display
        initial_recipes = await recipe_service.get_random_recipes(10)
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "recipes": initial_recipes}
        )
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        # Return a basic response if we encounter an error
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "recipes": []}
        )

@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    """Process chat messages and return recipe recommendations"""
    try:
        logger.info(f"Received chat message: {message}")
        
        # Extract ingredients from user message
        ingredients = recipe_recommender.extract_ingredients(message)
        logger.info(f"Extracted ingredients: {ingredients}")
        
        # Find recipes based on ingredients using ML algorithms
        recipes = await recipe_recommender.find_recipes_by_ingredients(ingredients)
        
        # Generate a response message
        if recipes:
            response = f"I found {len(recipes)} recipes with your ingredients: {', '.join(ingredients)}"
        else:
            response = f"I couldn't find recipes with exactly those ingredients. Here are some alternatives."
            recipes = await recipe_service.get_random_recipes(5)
        
        return templates.TemplateResponse(
            "chat_response.html", 
            {"request": request, "message": message, "response": response, "recipes": recipes}
        )
    except Exception as e:
        logger.error(f"Error in chat route: {e}")
        # Return a graceful error message
        error_recipes = await recipe_service.get_random_recipes(3)
        return templates.TemplateResponse(
            "chat_response.html", 
            {
                "request": request, 
                "message": message, 
                "response": "I had trouble processing your request, but here are some recipes you might like:", 
                "recipes": error_recipes
            }
        )

@app.get("/recipes/search")
async def search_recipes(query: str = ""):
    """Search recipes by name or ingredients"""
    try:
        return await recipe_service.search_recipes(query)
    except Exception as e:
        logger.error(f"Error in search route: {e}")
        return []

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 