from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from ..config.srs_config import config, SRSConfig
import json
from pathlib import Path

class SRSService:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.config = config
        self.state = self.load_state()

    def load_state(self) -> Dict[str, Any]:
        """Load SRS state from file"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_state(self):
        """Save SRS state to file"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def initialize_card_state(self, card_id: str) -> Dict[str, Any]:
        """Initialize state for a new card"""
        today = datetime.now().date().isoformat()
        return {
            "interval": 0,
            "repetitions": 0,
            "easiness": self.config.card_parameters.ease_factor,
            "due": today,
            "learning_step": 0,
            "lapses": 0,
            "last_review": today
        }

    def parse_interval(self, interval_str: str) -> timedelta:
        """Parse interval string (e.g., '10m', '1d') to timedelta"""
        value = int(interval_str[:-1])
        unit = interval_str[-1]
        if unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'd':
            return timedelta(days=value)
        raise ValueError(f"Invalid interval format: {interval_str}")

    def calculate_next_interval(self, card_state: Dict[str, Any], quality: int) -> timedelta:
        """Calculate next review interval based on quality and current state"""
        if card_state["learning_step"] < len(self.config.learning_parameters.learning_steps):
            # Card is still in learning phase
            if quality < 3:  # Failed
                if self.config.learning_parameters.fail_reset:
                    card_state["learning_step"] = 0
                return self.parse_interval(self.config.learning_parameters.learning_steps[0])
            else:
                next_step = card_state["learning_step"] + 1
                if next_step < len(self.config.learning_parameters.learning_steps):
                    return self.parse_interval(self.config.learning_parameters.learning_steps[next_step])
                # Graduate from learning
                card_state["learning_step"] = len(self.config.learning_parameters.learning_steps)
                return timedelta(days=self.config.card_parameters.initial_interval)
        
        # Card is in review phase
        if quality < 3:
            card_state["lapses"] += 1
            if card_state["lapses"] >= self.config.feedback_parameters.leech_threshold:
                card_state["is_leech"] = True
            card_state["easiness"] *= self.config.feedback_parameters.lapse_penalty
            return timedelta(days=self.config.card_parameters.minimum_interval)
        
        # Calculate new interval
        if card_state["interval"] == 0:
            interval = self.config.card_parameters.initial_interval
        else:
            modifier = self.config.feedback_parameters.interval_modifiers[
                self.config.feedback_parameters.response_scale[quality-1]
            ]
            interval = int(card_state["interval"] * card_state["easiness"] * modifier)
        
        # Apply bounds
        interval = max(self.config.card_parameters.minimum_interval,
                      min(interval, self.config.card_parameters.maximum_interval))
        
        return timedelta(days=interval)

    def update_card(self, card_id: str, quality: int) -> Dict[str, Any]:
        """Update card state based on review quality"""
        if card_id not in self.state:
            self.state[card_id] = self.initialize_card_state(card_id)
        
        card_state = self.state[card_id]
        next_interval = self.calculate_next_interval(card_state, quality)
        
        # Update state
        card_state["interval"] = next_interval.days
        card_state["last_review"] = datetime.now().date().isoformat()
        card_state["due"] = (datetime.now() + next_interval).date().isoformat()
        
        if quality >= 3:
            card_state["repetitions"] += 1
        else:
            card_state["repetitions"] = 0
        
        self.save_state()
        return card_state

    def get_due_cards(self, cards: List[Dict[str, Any]], include_new: bool = True) -> List[Dict[str, Any]]:
        """Get cards due for review"""
        today = datetime.now().date().isoformat()
        due_cards = []
        new_cards = []
        
        for card in cards:
            card_id = str(card["id"])
            if card_id not in self.state:
                if include_new and len(new_cards) < self.config.new_cards_per_day:
                    new_cards.append(card)
                continue
            
            if self.state[card_id]["due"] <= today:
                due_cards.append(card)
        
        # Apply daily limit
        total_cards = len(due_cards) + len(new_cards)
        if total_cards > self.config.daily_card_limit:
            due_cards = due_cards[:self.config.daily_card_limit]
            new_cards = []
        
        # Mix according to strategy
        if self.config.review_mix_strategy.strategy_type == "interleaved":
            # Interleave new cards with reviews
            mixed_cards = []
            new_idx = 0
            review_idx = 0
            while new_idx < len(new_cards) or review_idx < len(due_cards):
                if review_idx < len(due_cards):
                    mixed_cards.append(due_cards[review_idx])
                    review_idx += 1
                if new_idx < len(new_cards):
                    mixed_cards.append(new_cards[new_idx])
                    new_idx += 1
            return mixed_cards
        else:
            # Return in blocks: reviews first, then new cards
            return due_cards + new_cards 