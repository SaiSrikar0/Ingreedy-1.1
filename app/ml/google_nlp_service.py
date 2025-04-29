from google.cloud import language_v1
from typing import List, Dict, Any, Tuple, Optional
import logging
import os

logger = logging.getLogger(__name__)

class GoogleNLPService:
    """Service for Google Cloud Natural Language API integration"""
    
    def __init__(self):
        """Initialize the Google NLP service"""
        # Initialize the client
        self.client = language_v1.LanguageServiceClient()
        
        # Set up common food-related entity types
        self.food_entity_types = {
            language_v1.Entity.Type.OTHER,  # Most food items are classified as OTHER
            language_v1.Entity.Type.CONSUMER_GOOD
        }
    
    def extract_ingredients(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Extract ingredients from text using Google Cloud Natural Language API
        Returns: (ingredients_list, operators_list)
        """
        try:
            # Create document object
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            
            # Analyze entities
            response = self.client.analyze_entities(
                document=document,
                encoding_type=language_v1.EncodingType.UTF8
            )
            
            # Extract ingredients and operators
            ingredients = []
            operators = []
            
            for entity in response.entities:
                # Check if entity is likely to be a food item
                if entity.type_ in self.food_entity_types:
                    # Get the normalized name if available, otherwise use the original text
                    ingredient = entity.name.lower()
                    ingredients.append(ingredient)
                
                # Check for operators in the text
                if entity.name.lower() in ['and', 'or']:
                    operators.append(entity.name.lower())
            
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
            logger.error(f"Error in Google NLP ingredient extraction: {e}")
            return [], []
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text using Google Cloud Natural Language API
        Returns: Dictionary with sentiment scores
        """
        try:
            # Create document object
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            
            # Analyze sentiment
            response = self.client.analyze_sentiment(
                document=document,
                encoding_type=language_v1.EncodingType.UTF8
            )
            
            # Extract sentiment scores
            sentiment = response.document_sentiment
            
            return {
                'score': sentiment.score,
                'magnitude': sentiment.magnitude
            }
            
        except Exception as e:
            logger.error(f"Error in Google NLP sentiment analysis: {e}")
            return {'score': 0.0, 'magnitude': 0.0}
    
    def classify_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Classify text content using Google Cloud Natural Language API
        Returns: List of classification categories with confidence scores
        """
        try:
            # Create document object
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            
            # Classify text
            response = self.client.classify_text(
                document=document,
                encoding_type=language_v1.EncodingType.UTF8
            )
            
            # Extract categories and confidence scores
            categories = []
            for category in response.categories:
                categories.append({
                    'name': category.name,
                    'confidence': category.confidence
                })
            
            return categories
            
        except Exception as e:
            logger.error(f"Error in Google NLP text classification: {e}")
            return [] 