from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import time
import json
from pathlib import Path

# Base directory configuration
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
KANJI_DB_PATH = DATA_DIR / 'kanji.db'
CONFIG_PATH = DATA_DIR / 'srs_config.json'

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

class LearningTimeWindow(BaseModel):
    start_time: time = Field(default=time(9, 0))  # 9:00 AM
    end_time: time = Field(default=time(21, 0))   # 9:00 PM

class ReviewMixStrategy(BaseModel):
    strategy_type: str = Field(default="interleaved", description="interleaved or blocks")
    new_card_ratio: float = Field(default=0.2, description="Ratio of new cards to mix with reviews")

class CardParameters(BaseModel):
    initial_interval: int = Field(default=1, description="Initial interval in days")
    ease_factor: float = Field(default=2.5, description="Base ease factor")
    minimum_interval: int = Field(default=1, description="Minimum interval in days")
    maximum_interval: int = Field(default=365, description="Maximum interval in days")

class FeedbackParameters(BaseModel):
    response_scale: List[str] = Field(
        default=["Again", "Hard", "Good", "Easy"],
        description="Available response options"
    )
    interval_modifiers: dict = Field(
        default={
            "Again": 0.0,
            "Hard": 0.5,
            "Good": 1.0,
            "Easy": 1.5
        }
    )
    lapse_penalty: float = Field(default=0.5, description="Factor to reduce ease after lapse")
    leech_threshold: int = Field(default=8, description="Number of failures to mark as leech")

class LearningParameters(BaseModel):
    learning_steps: List[str] = Field(
        default=["10m", "1d"],
        description="Steps before graduating to review"
    )
    graduation_threshold: int = Field(default=2, description="Successes needed to graduate")
    fail_reset: bool = Field(default=True, description="Reset steps on failure")

class SRSConfig(BaseModel):
    # General user parameters
    daily_card_limit: int = Field(default=100)
    learning_time_window: LearningTimeWindow = Field(default_factory=LearningTimeWindow)
    new_cards_per_day: int = Field(default=20)
    review_mix_strategy: ReviewMixStrategy = Field(default_factory=ReviewMixStrategy)
    
    # Card parameters
    card_parameters: CardParameters = Field(default_factory=CardParameters)
    
    # Feedback parameters
    feedback_parameters: FeedbackParameters = Field(default_factory=FeedbackParameters)
    
    # Learning parameters
    learning_parameters: LearningParameters = Field(default_factory=LearningParameters)
    
    # Quiz parameters
    num_choices: int = Field(default=5)
    min_easiness: float = Field(default=1.3)
    default_easiness: float = Field(default=2.5)

def load_config() -> SRSConfig:
    """Load configuration from file or create default"""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
                return SRSConfig(**config_dict)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error loading config file: {e}")
        print("Creating new config file with default values")
    
    # Create new config with default values
    config = SRSConfig()
    save_config(config)
    return config

def save_config(config: SRSConfig):
    """Save configuration to file"""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config.dict(), f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config file: {e}")

# Global configuration instance
config = load_config() 