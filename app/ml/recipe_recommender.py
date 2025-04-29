import numpy as np
import pandas as pd
import re
from typing import List, Dict, Any, Tuple, Optional
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import pairwise_distances
import nltk
import logging
import random
from collections import Counter
from fuzzywuzzy import fuzz
from sklearn.metrics.pairwise import cosine_similarity

# Download NLTK resources
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except Exception as e:
    logging.warning(f"Error downloading NLTK resources: {e}")

# Import NLTK modules with error handling
try:
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
except Exception as e:
    logging.warning(f"Error importing NLTK modules: {e}")
    
    # Define fallback tokenizer if NLTK fails
    def word_tokenize(text):
        return text.lower().split()
    
    # Define fallback stopwords if NLTK fails
    class StopwordsProxy:
        def words(self, lang):
            common_stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 
                                'be', 'been', 'being', 'in', 'on', 'at', 'to', 'for', 'with', 
                                'by', 'about', 'like', 'through', 'over', 'before', 'after', 
                                'between', 'under', 'above', 'of', 'during', 'without', 'have', 
                                'has', 'had', 'do', 'does', 'did', 'can', 'could', 'will', 
                                'would', 'should', 'might', 'may', 'i', 'you', 'he', 'she', 
                                'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
            return common_stopwords
    
    stopwords = StopwordsProxy()

# Local imports
from app.api.recipe_service import RecipeService
from app.ml.google_nlp_service import GoogleNLPService

logger = logging.getLogger(__name__)

class RecipeRecommender:
    """
    Recipe recommendation system using ML algorithms:
    - K-means clustering to find recipes with exact/nearest ingredients
    - Hierarchical clustering as fallback when K-means fails
    - Google Cloud Natural Language API for ingredient extraction
    """
    
    def __init__(self, recipe_service: RecipeService):
        """Initialize the recipe recommender with a recipe service"""
        self.recipe_service = recipe_service
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.ingredient_vectorizer = None
        self.vectors = None
        self.recipe_data = None
        
        # Try to initialize Google NLP service, fall back to None if not available
        try:
            self.nlp_service = GoogleNLPService()
        except Exception as e:
            logger.warning(f"Google NLP service not available: {e}")
            self.nlp_service = None
        
        # Common cooking ingredients for better extraction
        self.common_ingredients = {
            # Indian staples
            'rice', 'dal', 'urad dal', 'moong dal', 'toor dal', 'chana dal',
            'wheat flour', 'besan', 'rava', 'semolina', 'poha', 'vermicelli',
            'idli rava', 'dosa batter', 'curd', 'yogurt', 'ghee', 'oil',
            
            # Spices and seasonings
            'turmeric', 'cumin', 'coriander', 'mustard seeds', 'fenugreek',
            'asafoetida', 'cardamom', 'cinnamon', 'cloves', 'pepper',
            'chili powder', 'garam masala', 'sambar powder', 'rasam powder',
            'curry leaves', 'coriander leaves', 'mint leaves',
            
            # Vegetables
            'potato', 'onion', 'tomato', 'carrot', 'beans', 'brinjal',
            'ladies finger', 'cabbage', 'cauliflower', 'peas', 'ginger',
            'garlic', 'green chili', 'curry leaves',
            
            # Lentils and pulses
            'chana', 'moong', 'masoor', 'urad', 'toor', 'rajma',
            
            # Dairy
            'milk', 'curd', 'yogurt', 'paneer', 'ghee', 'butter',
            
            # Nuts and dry fruits
            'cashew', 'almond', 'raisin', 'peanut', 'coconut',
            
            # Common ingredients
            'salt', 'sugar', 'jaggery', 'tamarind', 'lemon', 'water',
            
            # Western ingredients (for compatibility)
            'eggs', 'bread', 'milk', 'butter', 'flour', 'sugar', 'salt',
            'chicken', 'beef', 'pork', 'fish', 'pasta', 'cheese'
        }
        
        # Common recipe request phrases
        self.recipe_request_phrases = [
            "how to make", "recipe for", "how do i cook", "how do i make",
            "how to cook", "how to prepare", "recipe of", "dish with",
            "prepare", "want to make", "want to cook", "would like to make",
            "would like to cook", "looking for recipe", "looking for a recipe",
            "want a recipe", "want recipe", "need a recipe", "need recipe",
            "show me recipe", "show me a recipe", "cook with", "i have",
            "recipes with", "recipes using", "make with", "make using",
            # Indian specific phrases
            "how to make", "how to prepare", "how to cook", "recipe for",
            "dish with", "curry with", "sabzi with", "dal with", "rice with",
            "roti with", "paratha with", "dosa with", "idli with", "pongal with"
        ]
        
        # Create patterns for recipe requests
        self.recipe_request_pattern = re.compile(
            r"(?i)(" + "|".join(re.escape(phrase) for phrase in self.recipe_request_phrases) + r")\s+([a-zA-Z\s]+)"
        )
    
    def _load_common_ingredients(self) -> List[str]:
        """Load a list of common cooking ingredients"""
        try:
            # In a real app, this would read from a curated data file
            # For now, we'll use a simplified list
            return [
                "chicken", "beef", "rice", "pasta", "tomatoes", "onions", "garlic"
            ]
        except Exception as e:
            logger.error(f"Error loading ingredients: {e}")
            return ["chicken", "beef", "rice", "pasta", "tomatoes", "onions", "garlic"]
    
    def extract_ingredients(self, message: str) -> tuple:
        """
        Extract ingredient names from user message using Google Cloud Natural Language API
        Returns: Tuple of (ingredients_list, operators_list)
        """
        try:
            # Only try Google NLP service if it's available
            if self.nlp_service:
                ingredients, operators = self.nlp_service.extract_ingredients(message)
                if ingredients:
                    return ingredients, operators
            
            # Fall back to basic extraction if Google NLP is not available or fails
            return self._extract_ingredients_fallback(message)
            
        except Exception as e:
            logger.error(f"Error in ingredient extraction: {e}")
            return self._extract_ingredients_fallback(message)
    
    def _extract_ingredients_fallback(self, message: str) -> Tuple[List[str], List[str]]:
        """Fallback method for ingredient extraction without Google NLP"""
        try:
            # Basic ingredient extraction logic
            ingredients = []
            operators = []
            
            # Split message into words and clean it
            message = message.lower().strip()
            
            # Handle simple ingredient lists with "and" or commas
            if " and " in message:
                parts = message.split(" and ")
                for part in parts:
                    part = part.strip()
                    if part in self.common_ingredients:
                        ingredients.append(part)
                        if len(ingredients) > 1:
                            operators.append("and")
            elif "," in message:
                parts = message.split(",")
                for part in parts:
                    part = part.strip()
                    if part in self.common_ingredients:
                        ingredients.append(part)
                        if len(ingredients) > 1:
                            operators.append("and")
            else:
                # Split message into words
                words = message.split()
                
                # Look for ingredients and operators
                for i, word in enumerate(words):
                    # Check for operators
                    if word in ['and', 'or']:
                        operators.append(word)
                    
                    # Check for ingredients
                    if word in self.common_ingredients:
                        ingredients.append(word)
                    
                    # Check for two-word ingredients
                    if i < len(words) - 1:
                        two_word = f"{word} {words[i+1]}"
                        if two_word in self.common_ingredients:
                            ingredients.append(two_word)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_ingredients = []
            for ingredient in ingredients:
                if ingredient not in seen:
                    seen.add(ingredient)
                    unique_ingredients.append(ingredient)
            
            # Ensure we have n-1 operators for n ingredients
            if len(unique_ingredients) > 1 and len(operators) < len(unique_ingredients) - 1:
                # Default to AND for missing operators
                operators.extend(['and'] * (len(unique_ingredients) - 1 - len(operators)))
            
            return unique_ingredients, operators
            
        except Exception as e:
            logger.error(f"Error in fallback ingredient extraction: {e}")
            return [], []
    
    def _preprocess_recipes(self, recipes: List[Dict[str, Any]]) -> pd.DataFrame:
        """Preprocess recipes for ML algorithms"""
        # Convert to DataFrame
        if not recipes:
            return pd.DataFrame()
        
        df = pd.DataFrame(recipes)
        
        # Extract ingredient names as strings
        df['ingredient_names'] = df['ingredients'].apply(
            lambda ingredients: ' '.join([
                re.sub(r'[^\w\s]', '', ingredient['name'].lower())
                for ingredient in ingredients
            ])
        )
        
        return df
    
    def _vectorize_ingredients(self, df: pd.DataFrame) -> np.ndarray:
        """Convert ingredient text to TF-IDF vectors"""
        if df.empty:
            return np.array([])
        
        # Fit vectorizer if needed
        if self.ingredient_vectorizer is None:
            self.ingredient_vectorizer = TfidfVectorizer(stop_words='english')
            vectors = self.ingredient_vectorizer.fit_transform(df['ingredient_names'])
        else:
            vectors = self.ingredient_vectorizer.transform(df['ingredient_names'])
        
        return vectors
    
    def _vectorize_user_ingredients(self, ingredients: List[str]) -> np.ndarray:
        """Convert user ingredients to the same vector space as recipes"""
        if not ingredients or self.ingredient_vectorizer is None:
            return np.zeros((1, 1))
        
        # Join ingredients into a single string
        ingredient_text = ' '.join(ingredients)
        
        # Transform using the same vectorizer
        return self.ingredient_vectorizer.transform([ingredient_text])
    
    async def _kmeans_clustering(self, recipes_df: pd.DataFrame, user_vector: np.ndarray, 
                               k: int = 5) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Apply K-means clustering to find recipes closest to user ingredients
        Returns: (matching_recipes, success_flag)
        """
        if recipes_df.empty or user_vector.shape[1] <= 1:
            return [], False
        
        # Get recipe vectors
        recipe_vectors = self._vectorize_ingredients(recipes_df)
        
        if recipe_vectors.shape[0] == 0:
            return [], False
        
        # Calculate cosine similarity between user vector and recipe vectors
        similarities = cosine_similarity(user_vector, recipe_vectors)[0]
        
        # Get top k most similar recipes
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        # Get the corresponding recipes
        matching_recipes = recipes_df.iloc[top_k_indices].to_dict('records')
        
        return matching_recipes, True
    
    async def _hierarchical_clustering(self, recipes_df: pd.DataFrame, user_vector: np.ndarray, 
                                     threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Apply Hierarchical clustering as a fallback when K-means fails
        """
        if recipes_df.empty or user_vector.shape[1] <= 1:
            return []
        
        # Get recipe vectors
        recipe_vectors = self._vectorize_ingredients(recipes_df)
        
        if recipe_vectors.shape[0] == 0:
            return []
        
        # Calculate cosine similarity between user vector and recipe vectors
        similarities = cosine_similarity(user_vector, recipe_vectors)[0]
        
        # Get recipes above similarity threshold
        matching_indices = np.where(similarities > threshold)[0]
        
        if len(matching_indices) == 0:
            # If no recipes above threshold, return the 5 most similar ones
            matching_indices = np.argsort(similarities)[-5:][::-1]
        
        # Get the corresponding recipes
        matching_recipes = recipes_df.iloc[matching_indices].to_dict('records')
        
        # Sort by similarity score
        matching_recipes = sorted(
            zip(matching_recipes, similarities[matching_indices]),
            key=lambda x: x[1],
            reverse=True
        )
        matching_recipes = [recipe for recipe, _ in matching_recipes]
        
        return matching_recipes
    
    async def find_recipes_by_ingredients(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Main method to find recipes based on user ingredients
        Uses K-means first, falls back to Hierarchical clustering if needed
        """
        if not ingredients:
            # No ingredients provided, return random recipes
            return await self.recipe_service.get_random_recipes(5)
        
        # Extract operators if this is a tuple with ingredients and operators
        operators = []
        if isinstance(ingredients, tuple) and len(ingredients) == 2:
            ingredients, operators = ingredients
        
        # First try to get recipes with exact ingredients from API
        api_recipes = await self.recipe_service.get_recipes_by_ingredients(ingredients, operators)
        
        if api_recipes:
            return api_recipes
        
        # If no exact matches from API, try ML algorithms on our local data
        
        # Get all available recipes
        if self.recipe_service.recipes_df is not None and not self.recipe_service.recipes_df.empty:
            all_recipes = self.recipe_service.recipes_df.to_dict('records')
        else:
            # Fetch some recipes to work with
            all_recipes = await self.recipe_service.get_random_recipes(100)
        
        # Preprocess recipes
        recipes_df = self._preprocess_recipes(all_recipes)
        
        if recipes_df.empty:
            return []
        
        # Create vector for user ingredients
        user_vector = self._vectorize_user_ingredients(ingredients)
        
        # Try K-means clustering first
        kmeans_results, kmeans_success = await self._kmeans_clustering(recipes_df, user_vector)
        
        if kmeans_success and kmeans_results:
            # Prioritize Indian recipes in the results
            return sorted(kmeans_results, 
                key=lambda x: (
                    not self.recipe_service._is_priority_source(x.get('sourceUrl', '')),
                    not self.recipe_service._is_indian_recipe(x),
                    sum(1 for ing in ingredients 
                        if any(ing in i['name'].lower() or i['name'].lower() in ing 
                            for i in x['ingredients']))
                )
            )
        
        # If K-means fails, use Hierarchical clustering
        hierarchical_results = await self._hierarchical_clustering(recipes_df, user_vector)
        
        # Prioritize Indian recipes in the results
        return sorted(hierarchical_results, 
            key=lambda x: (
                not self.recipe_service._is_priority_source(x.get('sourceUrl', '')),
                not self.recipe_service._is_indian_recipe(x),
                sum(1 for ing in ingredients 
                    if any(ing in i['name'].lower() or i['name'].lower() in ing 
                        for i in x['ingredients']))
            )
        )
    
    def is_asking_for_recipe(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if the user is asking for a specific recipe.
        Returns: (is_asking_for_recipe, recipe_name)
        """
        # First check if this is general conversation
        if self.is_general_conversation(text.lower()):
            return False, None
        
        # Check for Indian recipe specific patterns
        indian_recipe_patterns = [
            r"(?i)how to make (dosa|idli|sambar|rasam|curry|biryani|pulao|roti|naan|paratha|puri|pongal|upma|poha|vada|pakora|samosa)",
            r"(?i)recipe for (dosa|idli|sambar|rasam|curry|biryani|pulao|roti|naan|paratha|puri|pongal|upma|poha|vada|pakora|samosa)",
            r"(?i)how to prepare (dosa|idli|sambar|rasam|curry|biryani|pulao|roti|naan|paratha|puri|pongal|upma|poha|vada|pakora|samosa)",
            r"(?i)how to cook (dosa|idli|sambar|rasam|curry|biryani|pulao|roti|naan|paratha|puri|pongal|upma|poha|vada|pakora|samosa)"
        ]
        
        for pattern in indian_recipe_patterns:
            match = re.search(pattern, text)
            if match:
                return True, match.group(1)
        
        # Check for "what can I make with" pattern - this should NOT be treated as asking for a specific recipe
        ingredient_request_patterns = [
            r"(?i)what can i make with\s+(.+)",
            r"(?i)what can i cook with\s+(.+)",
            r"(?i)recipes (using|with|containing)\s+(.+)",
            r"(?i)dishes? with\s+(.+)",
            r"(?i)i have\s+(.+)",
            r"(?i)cook with\s+(.+)",
            # Indian specific patterns
            r"(?i)what indian dish can i make with\s+(.+)",
            r"(?i)indian recipes with\s+(.+)",
            r"(?i)how to use\s+(.+)\s+in indian cooking",
            r"(?i)what to make with\s+(.+)\s+indian style"
        ]
        
        for pattern in ingredient_request_patterns:
            if re.search(pattern, text):
                return False, None
        
        # If the text is just a single food item, it's likely asking for recipes with that ingredient
        # rather than a specific recipe name
        if len(text.split()) == 1 and text.lower() in self.common_ingredients:
            return False, None
        
        # Try to match recipe request patterns
        match = self.recipe_request_pattern.search(text)
        if match:
            recipe_name = match.group(2).strip()
            if recipe_name:
                return True, recipe_name
                
        # Look for direct recipe names
        direct_recipe_pattern = re.compile(r"(?i)(?:^|[^\w])([\w\s]+recipe|[\w\s]+dish)")
        direct_match = direct_recipe_pattern.search(text)
        if direct_match:
            recipe_name = direct_match.group(1).strip()
            if recipe_name:
                return True, recipe_name
                
        # Check for asking about a specific food item
        # This is a more relaxed check - just look for food items that might be recipes
        for ingredient in self.common_ingredients:
            # If the ingredient is mentioned as part of a phrase like "chicken curry" or "pasta carbonara"
            ingredient_pattern = re.compile(rf"(?i)\b{re.escape(ingredient)}\s+([a-zA-Z\s]+)")
            ingredient_match = ingredient_pattern.search(text)
            if ingredient_match:
                recipe_name = f"{ingredient} {ingredient_match.group(1).strip()}"
                # Only return if it seems like a recipe name (e.g., "chicken curry", not just "chicken")
                if len(recipe_name.split()) > 1:
                    return True, recipe_name
        
        return False, None
    
    def is_general_conversation(self, text: str) -> bool:
        """Check if the message is general conversation rather than a recipe request"""
        # Common greetings and general phrases
        greetings = [
            "hi", "hello", "hey", "howdy", "hola", "greetings", "good morning", 
            "good afternoon", "good evening", "what's up", "how are you", 
            "how's it going", "how do you do", "nice to meet you", "thanks", 
            "thank you", "thx", "ty"
        ]
        
        # Very short messages are likely conversational
        if len(text.split()) < 3:
            for greeting in greetings:
                if greeting in text.lower():
                    return True
            # Very short messages like "hi" or "hey"
            if len(text) < 10:
                return True
        
        # Check for common conversational phrases
        conversational_phrases = [
            "how are you", "what's new", "what do you do", "who are you",
            "what can you do", "tell me about yourself", "nice to meet you",
            "good to see you", "thanks", "thank you", "appreciate it",
            "you're welcome", "no problem", "that's great", "awesome", "cool",
            "nice", "good", "great", "how's your day", "how was your day",
            "what's happening", "what's going on", "bye", "goodbye", "see you",
            "talk to you later", "ttyl", "help", "can you help", "please help"
        ]
        
        for phrase in conversational_phrases:
            if phrase in text.lower():
                return True
                
        return False
    
    async def get_conversational_response(self, text: str) -> str:
        """Generate a friendly response for general conversation"""
        text_lower = text.lower()
        
        # Handle different types of conversational messages
        
        # Greetings
        if any(greeting in text_lower for greeting in ["hi", "hello", "hey", "howdy", "hola", "greetings"]):
            responses = [
                "Hello there! 👋 I'm Ingreedy, your cooking assistant. What would you like to cook today?",
                "Hi! I can help you find delicious recipes based on ingredients you have. What are you in the mood for?",
                "Hey! Ready to cook something amazing? Tell me what ingredients you have or what dish you'd like to make!",
                "Hello! I'd be happy to suggest some recipes for you. What ingredients do you have on hand?"
            ]
            return random.choice(responses)
            
        # Time-based greetings
        elif any(greeting in text_lower for greeting in ["good morning", "good afternoon", "good evening"]):
            if "morning" in text_lower:
                responses = [
                    "Good morning! ☀️ How about something delicious for breakfast?",
                    "Morning! Ready for some cooking inspiration to start your day?"
                ]
            elif "afternoon" in text_lower:
                responses = [
                    "Good afternoon! Looking for lunch ideas or planning dinner?",
                    "Afternoon! What kind of meal are you planning today?"
                ]
            else:  # evening
                responses = [
                    "Good evening! Time for a delightful dinner. What are you in the mood for?",
                    "Evening! Ready to cook something special for dinner tonight?"
                ]
            return random.choice(responses)
            
        # Thank you messages
        elif any(thanks in text_lower for thanks in ["thanks", "thank you", "thx", "ty", "appreciate"]):
            responses = [
                "You're welcome! 😊 Anything else you'd like to cook?",
                "Happy to help! Let me know if you need more recipe ideas.",
                "Anytime! Cooking is more fun when we do it together. Need anything else?",
                "My pleasure! I'm here whenever you need cooking inspiration."
            ]
            return random.choice(responses)
            
        # Help requests
        elif "help" in text_lower or "can you" in text_lower or "how do you" in text_lower:
            return "I can help you find recipes based on ingredients you have, or I can provide detailed instructions for specific dishes. Just let me know what ingredients you have or what dish you'd like to make!"
            
        # Goodbyes
        elif any(bye in text_lower for bye in ["bye", "goodbye", "see you", "talk to you later", "ttyl"]):
            responses = [
                "Goodbye! Come back when you're hungry again! 👋",
                "See you later! Happy cooking! 🍳",
                "Talk to you soon! Enjoy your meal! 🍽️"
            ]
            return random.choice(responses)
            
        # Default response for other conversation
        else:
            responses = [
                "I'm here to help with recipe ideas! Tell me what ingredients you have or what dish you'd like to make.",
                "I'm your friendly recipe assistant! What would you like to cook today?",
                "Looking for cooking inspiration? I can suggest recipes based on ingredients or help you make a specific dish.",
                "Tell me what ingredients you have, and I'll find you something delicious to make!"
            ]
            return random.choice(responses)
    
    async def find_recipe_by_name(self, recipe_name: str) -> List[Dict[str, Any]]:
        """
        Find recipes matching a specific name
        """
        if not recipe_name:
            return []
        
        # Search for recipe by name
        recipes = await self.recipe_service.search_recipes(recipe_name)
        
        # If we got results, return them
        if recipes:
            return recipes
            
        # If we didn't get results, try to extract key terms
        key_terms = recipe_name.split()
        key_terms = [term for term in key_terms if len(term) > 3]
        
        # If we have key terms, try searching with them
        if key_terms:
            for term in key_terms:
                recipes = await self.recipe_service.search_recipes(term)
                if recipes:
                    return recipes
        
        # If all else fails, return random recipes
        return await self.recipe_service.get_random_recipes(5) 