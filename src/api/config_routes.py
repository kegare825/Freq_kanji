from fastapi import APIRouter, HTTPException
from src.config.srs_config import (
    SRSConfig, load_config, save_config,
    LearningTimeWindow, ReviewMixStrategy,
    CardParameters, FeedbackParameters,
    LearningParameters
)
from typing import Optional
import json
from datetime import time

router = APIRouter(prefix="/config", tags=["configuration"])

@router.get("/", response_model=SRSConfig)
async def get_config():
    """Get current SRS configuration"""
    return load_config()

@router.put("/", response_model=SRSConfig)
async def update_config(config: SRSConfig):
    """Update entire SRS configuration"""
    save_config(config)
    return config

@router.patch("/general", response_model=SRSConfig)
async def update_general_params(
    daily_card_limit: Optional[int] = None,
    new_cards_per_day: Optional[int] = None,
    num_choices: Optional[int] = None
):
    """Update general parameters"""
    config = load_config()
    if daily_card_limit is not None:
        config.daily_card_limit = daily_card_limit
    if new_cards_per_day is not None:
        config.new_cards_per_day = new_cards_per_day
    if num_choices is not None:
        config.num_choices = num_choices
    save_config(config)
    return config

@router.patch("/learning-time", response_model=SRSConfig)
async def update_learning_time(window: LearningTimeWindow):
    """Update learning time window"""
    config = load_config()
    config.learning_time_window = window
    save_config(config)
    return config

@router.patch("/review-strategy", response_model=SRSConfig)
async def update_review_strategy(strategy: ReviewMixStrategy):
    """Update review mix strategy"""
    config = load_config()
    config.review_mix_strategy = strategy
    save_config(config)
    return config

@router.patch("/card-parameters", response_model=SRSConfig)
async def update_card_parameters(params: CardParameters):
    """Update card parameters"""
    config = load_config()
    config.card_parameters = params
    save_config(config)
    return config

@router.patch("/feedback-parameters", response_model=SRSConfig)
async def update_feedback_parameters(params: FeedbackParameters):
    """Update feedback parameters"""
    config = load_config()
    config.feedback_parameters = params
    save_config(config)
    return config

@router.patch("/learning-parameters", response_model=SRSConfig)
async def update_learning_parameters(params: LearningParameters):
    """Update learning parameters"""
    config = load_config()
    config.learning_parameters = params
    save_config(config)
    return config

def time_to_str(t):
    return t.strftime('%H:%M:%S') if isinstance(t, time) else t 