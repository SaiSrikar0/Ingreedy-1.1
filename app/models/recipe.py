from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Recipe:
    """Recipe data model"""
    title: str
    ingredients: List[str]
    instructions: List[str]
    cooking_time: Optional[int] = None  # in minutes
    servings: Optional[int] = None
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    is_indian: bool = False
    source: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert recipe to dictionary"""
        return {
            "title": self.title,
            "ingredients": self.ingredients,
            "instructions": self.instructions,
            "cooking_time": self.cooking_time,
            "servings": self.servings,
            "source_url": self.source_url,
            "image_url": self.image_url,
            "is_indian": self.is_indian,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Recipe':
        """Create recipe from dictionary"""
        return cls(
            title=data.get("title", ""),
            ingredients=data.get("ingredients", []),
            instructions=data.get("instructions", []),
            cooking_time=data.get("cooking_time"),
            servings=data.get("servings"),
            source_url=data.get("source_url"),
            image_url=data.get("image_url"),
            is_indian=data.get("is_indian", False),
            source=data.get("source")
        ) 