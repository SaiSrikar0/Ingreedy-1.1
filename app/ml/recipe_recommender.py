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

logger = logging.getLogger(__name__)

class RecipeRecommender:
    """
    Recipe recommendation system using ML algorithms:
    - K-means clustering to find recipes with exact/nearest ingredients
    - Hierarchical clustering as fallback when K-means fails
    """
    
    def __init__(self, recipe_service: RecipeService):
        """Initialize the recipe recommender with a recipe service"""
        self.recipe_service = recipe_service
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.ingredient_vectorizer = None
        self.vectors = None
        self.recipe_data = None
        self.common_food_ingredients = [
            'salt', 'pepper', 'olive oil', 'garlic', 'onion', 'butter', 'sugar',
            'flour', 'egg', 'milk', 'water', 'chicken', 'beef', 'pork', 'tomato',
            'potato', 'carrot', 'celery', 'rice', 'pasta', 'bread', 'cheese', 
            'lemon', 'lime', 'vinegar', 'oil', 'basil', 'oregano', 'parsley',
            'thyme', 'cilantro', 'cumin', 'paprika', 'cinnamon', 'vanilla',
            'mushroom', 'bell pepper', 'broccoli', 'spinach', 'corn', 'beans',
            'avocado', 'bacon', 'sausage', 'shrimp', 'salmon', 'tuna', 'cream',
            'yogurt', 'sour cream', 'mayonnaise', 'mustard', 'ketchup', 'soy sauce',
            'wine', 'stock', 'broth', 'honey', 'maple syrup', 'chocolate', 'nuts',
            'lettuce', 'cabbage', 'cucumber', 'zucchini', 'eggplant', 'ginger',
            'garlic powder', 'onion powder', 'baking powder', 'baking soda',
            'yeast', 'noodles', 'apple', 'banana', 'orange', 'berries', 'grapes',
            'eggs', 'potatoes'  # Added common singular forms
        ]
        
        # Common cooking ingredients for better extraction
        self.common_ingredients = self._load_common_ingredients()
        
        # Common recipe request phrases
        self.recipe_request_phrases = [
            "how to make", "recipe for", "how do i cook", "how do i make",
            "how to cook", "how to prepare", "recipe of", "dish with",
            "prepare", "want to make", "want to cook", "would like to make",
            "would like to cook", "looking for recipe", "looking for a recipe",
            "want a recipe", "want recipe", "need a recipe", "need recipe",
            "show me recipe", "show me a recipe", "cook with", "i have",
            "recipes with", "recipes using", "make with", "make using"
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
                "chicken", "beef", "pork", "lamb", "fish", "shrimp", "tofu",
                "rice", "pasta", "noodles", "potatoes", "bread", "flour",
                "tomatoes", "onions", "garlic", "carrots", "peppers", "spinach",
                "broccoli", "cheese", "cream", "milk", "yogurt", "butter",
                "eggs", "oil", "vinegar", "soy sauce", "sugar", "salt", "pepper",
                "mushrooms", "corn", "beans", "lentils", "chickpeas", "herbs",
                "basil", "cilantro", "parsley", "thyme", "rosemary", "oregano",
                "cumin", "paprika", "cinnamon", "lemon", "lime", "orange",
                "apples", "berries", "chocolate", "vanilla", "honey", "nuts",
                "almonds", "peanuts", "walnuts", "bacon", "sausage", "quinoa",
                "avocado", "cucumber", "zucchini", "eggplant", "cauliflower",
                "cabbage", "kale", "celery", "coriander", "curry", "chili",
                "mustard", "olives", "peas", "ginger", "asparagus", "coconut",
                "cream cheese", "sour cream", "mozzarella", "cheddar", "parmesan",
                "feta", "goat cheese", "lettuce", "arugula", "fennel", "beets",
                "sweet potatoes", "pomegranate", "mango", "pineapple", "banana",
                "peach", "pear", "plum", "figs", "dates", "raisins", "cranberries",
                "blueberries", "strawberries", "raspberries", "blackberries",
                "paneer", "ghee", "turmeric", "cardamom", "cloves", "cinnamon",
                "star anise", "fennel seeds", "mustard seeds", "mint", "dill",
                "capers", "anchovies", "tuna", "salmon", "cod", "tilapia",
                "turkey", "duck", "goose", "quail", "venison", "bison", "veal",
                "ham", "prosciutto", "salami", "pepperoni", "chorizo", "soy",
                "tempeh", "seitan", "lentils", "black beans", "kidney beans",
                "pinto beans", "chickpeas", "split peas", "barley", "oats",
                "bulgur", "farro", "couscous", "polenta", "ketchup", "mayonnaise",
                "relish", "jam", "jelly", "maple syrup", "pumpkin", "squash",
                "zest", "greens", "chard", "endive", "brie", "camembert",
                "blue cheese", "wheat", "baking soda", "baking powder", "yeast",
                "cream of tartar", "cocoa", "molasses", "caramel", "cream",
                "vanilla extract", "almond extract", "sprinkles", "food coloring",
                "icing", "frosting", "pudding", "gelatin", "jam", "syrup",
                "custard", "paste", "sauce", "broth", "stock", "puff pastry",
                "phyllo dough", "tortillas", "pita", "naan", "focaccia",
                "sourdough", "rye", "white bread", "whole wheat", "cereal"
            ]
        except Exception as e:
            logger.error(f"Error loading ingredients: {e}")
            return ["chicken", "beef", "rice", "pasta", "tomatoes", "onions", "garlic"]
    
    def extract_ingredients(self, message: str) -> List[str]:
        """Extract ingredient names from user message"""
        try:
            # If message is a single word that might be an ingredient, handle it directly
            message = message.strip().lower()
            if len(message.split()) == 1 and len(message) > 2:
                # Single word that might be an ingredient - return it directly
                single_word = message
                
                # Check for plural forms
                if single_word.endswith('es') and len(single_word) > 4:
                    singular = single_word[:-2]  # Remove 'es'
                    if singular in self.common_food_ingredients:
                        return [singular]
                elif single_word.endswith('s') and len(single_word) > 3:
                    singular = single_word[:-1]  # Remove 's'
                    if singular in self.common_food_ingredients:
                        return [singular]
                
                # Check if it's in common ingredients list
                if single_word in self.common_food_ingredients:
                    return [single_word]
                
                # Special cases for common ingredients
                if single_word == 'potato' or single_word == 'potatoes':
                    return ['potatoes']
                if single_word == 'egg' or single_word == 'eggs':
                    return ['eggs']
                if single_word == 'tomato' or single_word == 'tomatoes':
                    return ['tomatoes']
                if single_word == 'onion' or single_word == 'onions':
                    return ['onions']
                
                # If it's not a common plural/singular case, still return it as potential ingredient
                return [single_word]
            
            # Special case for common ingredient combinations
            if "eggs and potatoes" in message or "potatoes and eggs" in message:
                return ["eggs", "potatoes"]
            if "eggs and potato" in message or "potato and eggs" in message:
                return ["eggs", "potatoes"]
            if "egg and potatoes" in message or "potatoes and egg" in message:
                return ["eggs", "potatoes"]
            if "egg and potato" in message or "potato and egg" in message:
                return ["eggs", "potatoes"]
                
            # Process common conjunctions to better extract multiple ingredients
            ingredients = []
            
            # First split by common separators like commas and "and"
            parts = re.split(r',|\sand\s|\swith\s|\splus\s', message)
            for part in parts:
                part = part.strip()
                if part:
                    # Check for known ingredients in each part
                    for ingredient in self.common_food_ingredients:
                        if ingredient in part:
                            ingredients.append(ingredient)
                            break
                    else:
                        # If no known ingredient was found, add the whole part for further processing
                        if len(part.split()) <= 2:  # Only add if it's a short phrase
                            ingredients.append(part)
            
            # If we found ingredients through the split method, return them
            if ingredients:
                # Standard normalization for common ingredients
                normalized_ingredients = []
                for ing in ingredients:
                    if ing == 'potato' or ing == 'potatoes':
                        normalized_ingredients.append('potatoes')
                    elif ing == 'egg' or ing == 'eggs':
                        normalized_ingredients.append('eggs') 
                    elif ing == 'tomato' or ing == 'tomatoes':
                        normalized_ingredients.append('tomatoes')
                    elif ing == 'onion' or ing == 'onions':
                        normalized_ingredients.append('onions')
                    else:
                        normalized_ingredients.append(ing)
                
                # Remove duplicates while preserving order
                seen = set()
                return [x for x in normalized_ingredients if not (x in seen or seen.add(x))]
            
            # Tokenize message
            tokens = word_tokenize(message.lower())
            
            try:
                stop_words = set(stopwords.words('english'))
            except:
                # Fallback if stopwords fail
                stop_words = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
                                'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him',
                                'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
                                'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
                                'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am',
                                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
                                'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the',
                                'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of',
                                'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
                                'through', 'during', 'before', 'after', 'above', 'below', 'to',
                                'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
                                'again', 'further', 'then', 'once', 'here', 'there', 'when',
                                'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
                                'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
                                'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
                                'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've',
                                'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn',
                                'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn',
                                'wasn', 'weren', 'won', 'wouldn', 'make', 'using', 'use', 'can', 'want',
                                'like', 'need', 'got', 'get', 'would', 'could', 'should', 'recipe',
                                'cook', 'cooking', 'made', 'help', 'please', 'thank', 'thanks',
                                'hi', 'hello', 'hey', 'how', 'what', 'something', 'anything',
                                'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing'])
            
            # Filter tokens to find ingredients
            ingredients = []
            
            # Direct extraction of ingredients from message
            for word in message.lower().split():
                # Check if word is in common ingredients
                if word in self.common_food_ingredients:
                    ingredients.append(word)
            
            # Look for common ingredients in user message
            for ingredient in self.common_food_ingredients:
                if ingredient.lower() in message.lower() and ingredient not in ingredients:
                    ingredients.append(ingredient)
            
            # Look for phrases that might be ingredients
            for i in range(len(tokens)):
                if tokens[i] not in stop_words:
                    # Check single words
                    if tokens[i] in self.common_food_ingredients and tokens[i] not in ingredients:
                        ingredients.append(tokens[i])
                    
                    # Check two-word phrases
                    if i < len(tokens) - 1:
                        two_word = f"{tokens[i]} {tokens[i+1]}"
                        if two_word in self.common_food_ingredients and two_word not in ingredients:
                            ingredients.append(two_word)
            
            # Process specific ingredient keywords
            if 'chicken' in message.lower() and 'chicken' not in ingredients:
                ingredients.append('chicken')
            if 'broccoli' in message.lower() and 'broccoli' not in ingredients:
                ingredients.append('broccoli')
            if 'rice' in message.lower() and 'rice' not in ingredients:
                ingredients.append('rice')
            if 'egg' in message.lower() or 'eggs' in message.lower():
                if 'egg' not in ingredients and 'eggs' not in ingredients:
                    ingredients.append('eggs')
            if 'potato' in message.lower() or 'potatoes' in message.lower():
                if 'potato' not in ingredients and 'potatoes' not in ingredients:
                    ingredients.append('potatoes')
            if 'tomato' in message.lower() or 'tomatoes' in message.lower():
                if 'tomato' not in ingredients and 'tomatoes' not in ingredients:
                    ingredients.append('tomatoes')
            if 'onion' in message.lower() or 'onions' in message.lower():
                if 'onion' not in ingredients and 'onions' not in ingredients:
                    ingredients.append('onions')
            
            # Remove duplicates while preserving order
            seen = set()
            unique_ingredients = [x for x in ingredients if not (x in seen or seen.add(x))]
            
            # If no ingredients found through normal methods, do a fallback extraction
            if not unique_ingredients:
                # Split the message by common delimiters and check each part
                parts = re.split(r'[,\s+]', message.lower())
                for part in parts:
                    clean_part = part.strip()
                    if clean_part and clean_part not in stop_words and len(clean_part) > 2:
                        # Check if it's a possible food item (not a very common word)
                        unique_ingredients.append(clean_part)
            
            return unique_ingredients
        
        except Exception as e:
            # Log the error and return basic extraction as fallback
            logging.error(f"Error in ingredient extraction: {e}")
            
            # Basic fallback extraction
            key_ingredients = []
            msg_lower = message.lower()
            
            # Check for single-word query that might be an ingredient
            if len(msg_lower.split()) == 1 and len(msg_lower) > 2:
                return [msg_lower]  # Return the single word as an ingredient
            
            # Check for key ingredients in the examples
            if 'chicken' in msg_lower:
                key_ingredients.append('chicken')
            if 'broccoli' in msg_lower:
                key_ingredients.append('broccoli')
            if 'rice' in msg_lower:
                key_ingredients.append('rice')
            if 'egg' in msg_lower or 'eggs' in msg_lower:
                key_ingredients.append('eggs')
            if 'potato' in msg_lower or 'potatoes' in msg_lower:
                key_ingredients.append('potatoes')
            if 'tomato' in msg_lower or 'tomatoes' in msg_lower:
                key_ingredients.append('tomatoes')
            if 'onion' in msg_lower or 'onions' in msg_lower:
                key_ingredients.append('onions')
            if 'butter' in msg_lower:
                key_ingredients.append('butter')
            if 'garlic' in msg_lower:
                key_ingredients.append('garlic')
            if 'cheese' in msg_lower:
                key_ingredients.append('cheese')
            if 'pasta' in msg_lower:
                key_ingredients.append('pasta')
            
            return key_ingredients if key_ingredients else [msg_lower.split()[0]]  # Return first word if nothing else found
    
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
        
        # Concatenate user vector with recipe vectors
        all_vectors = np.vstack([recipe_vectors.toarray(), user_vector.toarray()])
        
        # Apply K-means
        num_clusters = min(k, all_vectors.shape[0])
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        clusters = kmeans.fit_predict(all_vectors)
        
        # Find the cluster containing the user query
        user_cluster = clusters[-1]
        
        # Get recipes in the same cluster
        cluster_indices = np.where(clusters[:-1] == user_cluster)[0]
        
        if len(cluster_indices) == 0:
            return [], False
        
        # Get the corresponding recipes
        matching_recipes = recipes_df.iloc[cluster_indices].to_dict('records')
        
        return matching_recipes, True
    
    async def _hierarchical_clustering(self, recipes_df: pd.DataFrame, user_vector: np.ndarray, 
                                     threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Apply Hierarchical clustering as a fallback when K-means fails
        """
        if recipes_df.empty or user_vector.shape[1] <= 1:
            return []
        
        # Get recipe vectors
        recipe_vectors = self._vectorize_ingredients(recipes_df)
        
        if recipe_vectors.shape[0] == 0:
            return []
        
        # Calculate distance between user vector and recipe vectors
        distances = pairwise_distances(user_vector.toarray(), recipe_vectors.toarray(), metric='cosine')[0]
        
        # Sort recipes by distance (ascending)
        sorted_indices = np.argsort(distances)
        
        # Get recipes below distance threshold
        matching_indices = sorted_indices[distances[sorted_indices] < threshold]
        
        if len(matching_indices) == 0:
            # If no recipes below threshold, return the 5 closest ones
            matching_indices = sorted_indices[:5]
        
        # Get the corresponding recipes
        matching_recipes = recipes_df.iloc[matching_indices].to_dict('records')
        
        return matching_recipes
    
    async def find_recipes_by_ingredients(self, ingredients: List[str]) -> List[Dict[str, Any]]:
        """
        Main method to find recipes based on user ingredients
        Uses K-means first, falls back to Hierarchical clustering if needed
        """
        if not ingredients:
            # No ingredients provided, return random recipes
            return await self.recipe_service.get_random_recipes(5)
        
        # First try to get recipes with exact ingredients from API
        api_recipes = await self.recipe_service.get_recipes_by_ingredients(ingredients)
        
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
            return kmeans_results
        
        # If K-means fails, use Hierarchical clustering
        hierarchical_results = await self._hierarchical_clustering(recipes_df, user_vector)
        
        return hierarchical_results
    
    def is_asking_for_recipe(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if the user is asking for a specific recipe.
        Returns: (is_asking_for_recipe, recipe_name)
        """
        # First check if this is general conversation
        if self.is_general_conversation(text.lower()):
            return False, None
        
        # Check for "what can I make with" pattern - this should NOT be treated as asking for a specific recipe
        ingredient_request_patterns = [
            r"(?i)what can i make with\s+(.+)",
            r"(?i)what can i cook with\s+(.+)",
            r"(?i)recipes (using|with|containing)\s+(.+)",
            r"(?i)dishes? with\s+(.+)",
            r"(?i)i have\s+(.+)",
            r"(?i)cook with\s+(.+)",
        ]
        
        for pattern in ingredient_request_patterns:
            if re.search(pattern, text):
                return False, None
        
        # If the text is just a single food item, it's likely asking for recipes with that ingredient
        # rather than a specific recipe name
        if len(text.split()) == 1 and text.lower() in self.common_food_ingredients:
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