from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from dotenv import load_dotenv
import os
import logging
import re
import html
import random
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
import json

from app.api.recipe_service import RecipeService
from app.ml.recipe_recommender import RecipeRecommender
from app.api.models import ChatRequest, ChatResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

try:
    # Initialize FastAPI app
    app = FastAPI(title="Ingreedy - Recipe Chatbot", description="API for recipe recommendations based on ingredients")

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_dir):
        logger.error(f"Static directory not found: {static_dir}")
        raise FileNotFoundError(f"Static directory not found: {static_dir}")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Set up templates
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    if not os.path.exists(templates_dir):
        logger.error(f"Templates directory not found: {templates_dir}")
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")
    templates = Jinja2Templates(directory=templates_dir)

    # Initialize services
    try:
        recipe_service = RecipeService()
        recipe_recommender = RecipeRecommender(recipe_service)
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
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

    @app.post("/chat")
    async def chat(request: Request, chat_request: ChatRequest):
        """
        Process a chat message and return recipe recommendations or conversation
        """
        try:
            # Log the incoming message
            logger.info(f"Received chat message: {chat_request.message}")
            
            message = chat_request.message.strip()
            
            # Check for ingredient-based queries first (what can I make with X?)
            ingredient_patterns = [
                r"(?i)what\s+can\s+i\s+make\s+with\s+(.+)",
                r"(?i)what\s+can\s+i\s+cook\s+with\s+(.+)",
                r"(?i)recipes\s+(using|with|containing)\s+(.+)",
                r"(?i)dishes?\s+with\s+(.+)",
                r"(?i)i\s+have\s+(.+)",
                r"(?i)cook\s+with\s+(.+)",
            ]
            
            is_ingredient_query = False
            ingredient_extract_result = None
            
            for pattern in ingredient_patterns:
                match = re.search(pattern, message)
                if match:
                    is_ingredient_query = True
                    if "using|with|containing" in pattern:
                        ingredient_text = match.group(2)
                    else:
                        ingredient_text = match.group(1)
                    
                    logger.info(f"Detected ingredient query: {ingredient_text}")
                    ingredient_extract_result = recipe_recommender.extract_ingredients(ingredient_text)
                    break
            
            if is_ingredient_query and ingredient_extract_result:
                ingredients, operators = ingredient_extract_result
                if not ingredients:
                    return {
                        "response": "I couldn't identify any specific ingredients in your message. Please try again with ingredients like 'paneer', 'rice', 'chicken', etc.",
                        "recipes": await recipe_service.get_random_recipes(3)
                    }
                
                # Get recipes matching the ingredients
                recipes = await recipe_service.get_recipes_by_ingredients(ingredients, operators)
                
                if not recipes:
                    return {
                        "response": f"I couldn't find any recipes with {', '.join(ingredients)}. Here are some random recipes you might like:",
                        "recipes": await recipe_service.get_random_recipes(3)
                    }
                
                # Format the response
                ingredient_list = ", ".join(ingredients)
                response = f"I found some great recipes that use {ingredient_list}! Here are the top matches:"
                
                # Limit to top 5 recipes and format them
                top_recipes = recipes[:5]
                formatted_recipes = []
                for recipe in top_recipes:
                    # Get the main ingredients used in the recipe
                    recipe_ingredients = [ing['name'] for ing in recipe.get('ingredients', [])]
                    matching_ingredients = [ing for ing in ingredients if any(ing.lower() in ing_name.lower() for ing_name in recipe_ingredients)]
                    
                    formatted_recipe = {
                        "title": recipe.get('title', 'Untitled Recipe'),
                        "image": recipe.get('image', ''),
                        "sourceUrl": recipe.get('sourceUrl', ''),
                        "readyInMinutes": recipe.get('readyInMinutes', 0),
                        "servings": recipe.get('servings', 0),
                        "matchingIngredients": matching_ingredients,
                        "summary": recipe.get('summary', '')
                    }
                    formatted_recipes.append(formatted_recipe)
                
                return {
                    "response": response,
                    "recipes": formatted_recipes
                }
            
            # Handle other types of queries...
            return {
                "response": "I'm not sure how to help with that. Try asking about recipes with specific ingredients!",
                "recipes": await recipe_service.get_random_recipes(3)
            }
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {e}")
            return {
                "response": "Sorry, I encountered an error. Please try again.",
                "recipes": []
            }

    @app.post("/chat/simple")
    async def chat_simple(request: Request, chat_request: ChatRequest):
        """Simple chat endpoint that uses the recipe recommender"""
        try:
            # Initialize services
            recipe_service = RecipeService()
            recipe_recommender = RecipeRecommender(recipe_service)
            
            # Extract ingredients and operators from the message
            ingredients, operators = recipe_recommender.extract_ingredients(chat_request.message)
            
            if not ingredients:
                # No ingredients found, provide a helpful message and some random recipes
                random_recipes = await recipe_service.get_random_recipes(3)
                return JSONResponse({
                    "message": "I couldn't identify any specific ingredients in your message. Try mentioning ingredients like 'chicken', 'pasta', or 'tomatoes'. In the meantime, here are some popular recipes you might enjoy!",
                    "recipes": random_recipes
                })
            
            # Find recipes matching the ingredients and operators
            try:
                recipes = await recipe_recommender.find_recipes_by_ingredients((ingredients, operators))
                
                # Debug log for the recipes found
                if recipes:
                    logger.info(f"Found {len(recipes)} recipes. Top match: {recipes[0]['title']}")
                    # Log the ingredients of the top recipe for debugging
                    if 'ingredients' in recipes[0]:
                        recipe_ingredients = [ingredient.get('name', '') for ingredient in recipes[0]['ingredients']]
                        logger.info(f"Top recipe ingredients: {recipe_ingredients}")
                else:
                    logger.info("No recipes found matching the criteria")
            except Exception as e:
                logger.error(f"Error finding recipes: {str(e)}")
                recipes = []
            
            if not recipes:
                random_recipes = await recipe_service.get_random_recipes(3)
                return JSONResponse({
                    "message": f"I couldn't find recipes with exactly those ingredients ({', '.join(ingredients)}). Here are some other popular recipes you might enjoy!",
                    "recipes": random_recipes
                })
            
            # Format a nice response with the matched recipes
            ingredients_list = ", ".join(ingredients)
            message = f"I found some great recipes that use {ingredients_list}! Here are the top matches:"
            
            return JSONResponse({
                "message": message,
                "recipes": recipes[:5]  # Return top 5 matches
            })
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "An error occurred while processing your request"}
            )

    def format_recipe_response(recipe: Dict[str, Any]) -> str:
        """Format a recipe into a nice response message with HTML formatting"""
        title = recipe.get('title', 'Untitled Recipe')
        
        # Start with the title
        response = f"<h2>{title}</h2>"
        
        # Add image if available
        if recipe.get('image'):
            response += f"<img src='{recipe['image']}' alt='{title}' style='max-width:100%; border-radius:8px; margin:10px 0;'>"
        
        # Add preparation time and servings if available
        prep_info = []
        if recipe.get('readyInMinutes'):
            prep_info.append(f"⏱️ Ready in {recipe['readyInMinutes']} minutes")
        if recipe.get('servings'):
            prep_info.append(f"👥 Serves {recipe['servings']}")
        
        if prep_info:
            response += f"<p style='color:#666; font-style:italic;'>{' • '.join(prep_info)}</p>"
        
        # Add ingredients section
        response += "<h3>Ingredients</h3>"
        if recipe.get('extendedIngredients'):
            response += "<ul style='padding-left:20px;'>"
            for ingredient in recipe['extendedIngredients']:
                response += f"<li>{ingredient.get('original', '')}</li>"
            response += "</ul>"
        else:
            response += "<p>Ingredients information not available</p>"
        
        # Add instructions section
        response += "<h3>Instructions</h3>"
        if recipe.get('instructions'):
            # Clean up instructions and split into steps if needed
            instructions = recipe['instructions'].replace('<ol>', '').replace('</ol>', '').replace('<li>', '').replace('</li>', '')
            
            # Check if instructions are already in steps format
            if '<step>' in instructions or instructions.strip().startswith('1.'):
                # Already in steps, just clean up
                instructions = instructions.replace('<step>', '').replace('</step>', '')
                response += f"<ol style='padding-left:20px;'>{instructions}</ol>"
            else:
                # Try to split into steps by sentence
                import re
                steps = re.split(r'(?<=[.!?])\s+', instructions)
                steps = [step for step in steps if step.strip()]
                
                if steps:
                    response += "<ol style='padding-left:20px;'>"
                    for step in steps:
                        if step.strip():
                            response += f"<li>{step}</li>"
                    response += "</ol>"
                else:
                    # Just use the instructions as-is
                    response += f"<p>{instructions}</p>"
        else:
            response += "<p>Instructions not available</p>"
        
        # Add source attribution if available
        if recipe.get('sourceUrl'):
            response += f"<p><small>Source: <a href='{recipe['sourceUrl']}' target='_blank'>{recipe.get('sourceName', 'Recipe Source')}</a></small></p>"
        
        # Add a closing message
        response += "<p>Enjoy your meal! Feel free to ask about another recipe or ingredient.</p>"
        
        return response

    @app.get("/recipes/search")
    async def search_recipes(query: str = ""):
        """Search recipes by name or ingredients"""
        try:
            return await recipe_service.search_recipes(query)
        except Exception as e:
            logger.error(f"Error in search route: {e}")
            return []

    @app.get("/recipes/{recipe_id}")
    async def get_recipe_detail(recipe_id: int):
        """Get details for a specific recipe by ID"""
        try:
            recipe = await recipe_service.get_recipe_by_id(recipe_id)
            if recipe:
                return recipe
            else:
                raise HTTPException(status_code=404, detail="Recipe not found")
        except Exception as e:
            logger.error(f"Error fetching recipe {recipe_id}: {e}")
            raise HTTPException(status_code=500, detail="Error fetching recipe details")

    @app.get("/api/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}

    @app.get("/api/recipes/all")
    async def get_all_recipes():
        """Get all available recipes"""
        try:
            # Get all recipes from the recipe service
            recipes = await recipe_service.get_all_recipes()
            return recipes
        except Exception as e:
            logging.error(f"Error fetching all recipes: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch recipes")

    if __name__ == "__main__":
        port = int(os.getenv("PORT", 8000))
        uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

except Exception as e:
    logger.error(f"Failed to initialize application: {e}")
    raise 