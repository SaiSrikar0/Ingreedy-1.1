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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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
        ingredients = []
        
        for pattern in ingredient_patterns:
            match = re.search(pattern, message)
            if match:
                is_ingredient_query = True
                if "using|with|containing" in pattern:
                    ingredient_text = match.group(2)
                else:
                    ingredient_text = match.group(1)
                
                logger.info(f"Detected ingredient query: {ingredient_text}")
                ingredients = recipe_recommender.extract_ingredients(ingredient_text)
                break  # Found a match, no need to check other patterns
        
        # If no specific pattern matched, try general ingredient extraction
        if not is_ingredient_query:
            # Check if this is general conversation
            if recipe_recommender.is_general_conversation(message):
                conversational_response = await recipe_recommender.get_conversational_response(message)
                
                # Sometimes suggest a random recipe with conversational responses
                if random.random() < 0.25:  # 25% chance
                    random_recipes = await recipe_service.get_random_recipes(1)
                    if random_recipes:
                        recipe = random_recipes[0]
                        return templates.TemplateResponse(
                            "chat_response.html", 
                            {
                                "request": request,
                                "response": f"{conversational_response}\n\nBy the way, have you ever tried {recipe['title']}? It's delicious!",
                                "recipes": [recipe]
                            }
                        )
                
                return templates.TemplateResponse(
                    "chat_response.html", 
                    {
                        "request": request,
                        "response": conversational_response,
                        "recipes": []
                    }
                )
                
            # Check if the user is asking for a specific recipe
            is_recipe_request, recipe_name = recipe_recommender.is_asking_for_recipe(message)
            
            if is_recipe_request and recipe_name:
                logger.info(f"User is requesting recipe for: {recipe_name}")
                recipes = await recipe_recommender.find_recipe_by_name(recipe_name)
                
                if recipes:
                    # Format a nice response with the recipe details
                    recipe = recipes[0]  # Get the top match
                    formatted_response = format_recipe_response(recipe)
                    return templates.TemplateResponse(
                        "chat_response.html", 
                        {
                            "request": request,
                            "response": formatted_response,
                            "recipes": recipes[:5]
                        }
                    )
                else:
                    # No recipes found for the specific request
                    random_recipes = await recipe_service.get_random_recipes(3)
                    return templates.TemplateResponse(
                        "chat_response.html", 
                        {
                            "request": request,
                            "response": f"I couldn't find a recipe for '{recipe_name}'. Would you like to try one of these popular recipes instead?",
                            "recipes": random_recipes
                        }
                    )
            
            # Extract ingredients from the message
            ingredients = recipe_recommender.extract_ingredients(message)
        
        # Log the extracted ingredients
        logger.info(f"Extracted ingredients: {ingredients}")
        
        if not ingredients:
            # No ingredients found, provide a helpful message and some random recipes
            random_recipes = await recipe_service.get_random_recipes(3)
            return templates.TemplateResponse(
                "chat_response.html", 
                {
                    "request": request,
                    "response": "I couldn't identify any specific ingredients in your message. Try mentioning ingredients like 'chicken', 'pasta', or 'tomatoes'. In the meantime, here are some popular recipes you might enjoy!",
                    "recipes": random_recipes
                }
            )
            
        # Find recipes matching the ingredients
        recipes = await recipe_recommender.find_recipes_by_ingredients(ingredients)
        
        if not recipes:
            random_recipes = await recipe_service.get_random_recipes(3)
            return templates.TemplateResponse(
                "chat_response.html", 
                {
                    "request": request,
                    "response": f"I couldn't find recipes with exactly those ingredients ({', '.join(ingredients)}). Here are some other popular recipes you might enjoy!",
                    "recipes": random_recipes
                }
            )
            
        # Format a nice response with the matched recipes
        ingredients_list = ", ".join(ingredients)
        response_message = f"Great! I found {len(recipes)} recipes using {ingredients_list}. Here's the best match:"
        
        if len(recipes) > 0:
            # Add the top recipe details to the message
            response_message = f"{response_message}\n\n{format_recipe_response(recipes[0])}"
            
        return templates.TemplateResponse(
            "chat_response.html", 
            {
                "request": request,
                "response": response_message,
                "recipes": recipes[:5]
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/chat/simple")
async def chat_simple(request: Request, chat_request: ChatRequest):
    """
    Process a chat message and return simple text response instead of HTML
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
        ingredients = []
        
        for pattern in ingredient_patterns:
            match = re.search(pattern, message)
            if match:
                is_ingredient_query = True
                if "using|with|containing" in pattern:
                    ingredient_text = match.group(2)
                else:
                    ingredient_text = match.group(1)
                
                logger.info(f"Detected ingredient query: {ingredient_text}")
                ingredients = recipe_recommender.extract_ingredients(ingredient_text)
                break  # Found a match, no need to check other patterns
        
        # If no specific pattern matched, try general ingredient extraction
        if not is_ingredient_query:
            # Check if this is general conversation
            if recipe_recommender.is_general_conversation(message):
                conversational_response = await recipe_recommender.get_conversational_response(message)
                
                # Sometimes suggest a random recipe with conversational responses
                if random.random() < 0.25:  # 25% chance
                    random_recipes = await recipe_service.get_random_recipes(1)
                    if random_recipes:
                        recipe = random_recipes[0]
                        return JSONResponse({
                            "message": f"{conversational_response}\n\nBy the way, have you ever tried {recipe['title']}? It's delicious!",
                            "recipes": [recipe]
                        })
                
                return JSONResponse({
                    "message": conversational_response,
                    "recipes": []
                })
            
            # Check if the user is asking for a specific recipe
            is_recipe_request, recipe_name = recipe_recommender.is_asking_for_recipe(message)
            
            if is_recipe_request and recipe_name:
                logger.info(f"User is requesting recipe for: {recipe_name}")
                recipes = await recipe_recommender.find_recipe_by_name(recipe_name)
                
                if recipes:
                    # Get the top match
                    recipe = recipes[0]
                    response_message = f"I found a recipe for {recipe['title']}! It takes about {recipe.get('readyInMinutes', '?')} minutes to prepare and serves {recipe.get('servings', '?')}."
                    return JSONResponse({
                        "message": response_message,
                        "recipes": recipes[:5]
                    })
                else:
                    # No recipes found for the specific request
                    random_recipes = await recipe_service.get_random_recipes(3)
                    return JSONResponse({
                        "message": f"I couldn't find a recipe for '{recipe_name}'. Would you like to try one of these popular recipes instead?",
                        "recipes": random_recipes
                    })
            
            # Extract ingredients from the message
            ingredients = recipe_recommender.extract_ingredients(message)
        
        # Log the extracted ingredients
        logger.info(f"Extracted ingredients: {ingredients}")
        
        if not ingredients:
            # No ingredients found, provide a helpful message and some random recipes
            random_recipes = await recipe_service.get_random_recipes(3)
            return JSONResponse({
                "message": "I couldn't identify any specific ingredients in your message. Try mentioning ingredients like 'chicken', 'pasta', or 'tomatoes'. In the meantime, here are some popular recipes you might enjoy!",
                "recipes": random_recipes
            })
        
        # Find recipes matching the ingredients
        recipes = await recipe_recommender.find_recipes_by_ingredients(ingredients)
        
        if not recipes:
            random_recipes = await recipe_service.get_random_recipes(3)
            return JSONResponse({
                "message": f"I couldn't find recipes with exactly those ingredients ({', '.join(ingredients)}). Here are some other popular recipes you might enjoy!",
                "recipes": random_recipes
            })
        
        # Format a nice response with the matched recipes
        ingredients_list = ", ".join(ingredients)
        response_message = f"Great! I found {len(recipes)} recipes using {ingredients_list}. Here's the best match: {recipes[0]['title']}. It takes about {recipes[0].get('readyInMinutes', '?')} minutes to prepare and serves {recipes[0].get('servings', '?')}."
        
        return JSONResponse({
            "message": response_message,
            "recipes": recipes[:5]
        })
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 