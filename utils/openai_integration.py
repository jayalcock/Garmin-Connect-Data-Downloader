#!/usr/bin/env python3

"""
OpenAI integration for Garmin workout data analysis.

This module provides functions to send workout data to OpenAI's API
and get insights and recommendations based on the data.
"""

import os
import json
import datetime
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class OpenAIAnalyzer:
    """Class to handle OpenAI API interactions for workout data analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the OpenAI API client.
        
        Args:
            api_key: OpenAI API key. If None, will try to load from environment variable OPENAI_API_KEY.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
    
    def get_available_models(self) -> List[str]:
        """
        Get a list of available models from the OpenAI API.
        
        Returns:
            List of model IDs that can be used
        """
        if not self.is_ready():
            logger.error("OpenAI client not initialized. Check API key.")
            return []
            
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")
            return []
            
    def get_best_available_model(self) -> str:
        """
        Find the best available model to use for analysis.
        
        Returns:
            Model ID string for the best available model
        """
        preferred_models = [
            "gpt-4.1-mini",
            "gpt-4.1",
            "gpt-4.1-nano"
        ]
        
        try:
            available_models = self.get_available_models()
            
            # Find the first preferred model that's available
            for model in preferred_models:
                for available_model in available_models:
                    if model in available_model:  # Check if the model name contains our preferred model
                        logger.info(f"Using model: {available_model}")
                        return available_model
                        
            # If none of our preferred models are available, use the default
            logger.warning("No preferred models available, using default gpt-3.5-turbo")
            return "gpt-3.5-turbo"
        except Exception as e:
            logger.error(f"Error selecting model: {e}")
            return "gpt-3.5-turbo"  # Fallback to GPT-3.5 Turbo
    
    def is_ready(self) -> bool:
        """Check if the OpenAI client is properly initialized."""
        return self.client is not None
    
    def set_api_key(self, api_key: str) -> bool:
        """
        Set the OpenAI API key.
        
        Args:
            api_key: The OpenAI API key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.api_key = api_key
            self.client = OpenAI(api_key=self.api_key)
            return True
        except Exception as e:
            logger.error(f"Error setting API key: {e}")
            return False
    
    def format_workout_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format workout data for OpenAI analysis.
        
        Args:
            data: Raw workout data from Garmin
            
        Returns:
            Formatted data suitable for OpenAI analysis
        """
        formatted_data = {
            "date": data.get("date", "Unknown date"),
            "summary": {},
            "metrics": {},
            "analysis_request": "Please analyze this workout data and provide insights on performance, recovery, and training recommendations."
        }
        
        # Extract summary fields
        summary_fields = [
            "activityName", "activityType", "startTimeLocal", "durationInSeconds", 
            "distanceInMeters", "averagePace", "averageHeartRate", "maxHeartRate",
            "totalElevationGain", "totalElevationLoss", "averageStrideLength",
            "averageRunningCadenceInStepsPerMinute"
        ]
        
        for field in summary_fields:
            if field in data:
                formatted_data["summary"][field] = data[field]
        
        # Extract detailed metrics
        metric_fields = [
            "calories", "steps", "activeKilocalories", "bmrKilocalories",
            "wellnessEpochData", "intensityMinutes", "averageStressLevel",
            "maxStressLevel", "stressQualifier", "restingHeartRate"
        ]
        
        for field in metric_fields:
            if field in data:
                formatted_data["metrics"][field] = data[field]
        
        return formatted_data
    
    def analyze_workout(self, workout_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send workout data to OpenAI for analysis.
        
        Args:
            workout_data: Formatted workout data
            
        Returns:
            Analysis results from OpenAI, or None if an error occurs
        """
        if not self.is_ready():
            logger.error("OpenAI client not initialized. Check API key.")
            return None
        
        try:
            # Format the messages for the API request
            messages = [
                {"role": "system", "content": "You are a fitness coach and health analyst specializing in interpreting workout data. Provide insights on performance, trends, and actionable recommendations based on the data."},
                {"role": "user", "content": f"Here is my workout data from {workout_data.get('date', 'today')}:\n{json.dumps(workout_data, indent=2)}\n\nPlease analyze this data and provide insights."}
            ]
            
            # Get the best available model
            model = self.get_best_available_model()
            
            # Call the OpenAI Chat Completions API
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000
            )
            
            # Extract and return the response
            if response and response.choices and len(response.choices) > 0:
                analysis = response.choices[0].message.content
                return {
                    "date": workout_data.get("date", "Unknown date"),
                    "analysis": analysis,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            logger.warning("Empty response from OpenAI API.")
            return None
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error calling OpenAI API: {error_message}")
            
            # Check for specific error types
            if "model_not_found" in error_message:
                logger.info("Model not found. Will attempt to use a different model on next try.")
            elif "insufficient_quota" in error_message:
                logger.error("OpenAI API quota exceeded. Please check your billing information.")
            elif "invalid_api_key" in error_message:
                logger.error("Invalid API key. Please check your API key is correct.")
                
            return None
    
    def save_analysis(self, analysis: Dict[str, Any], output_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Save analysis results to a file.
        
        Args:
            analysis: Analysis results from OpenAI
            output_dir: Directory to save the analysis file (default: exports/analysis)
            
        Returns:
            Path to the saved file, or None if an error occurs
        """
        try:
            if not output_dir:
                output_dir = Path(__file__).parent.parent / "exports" / "analysis"
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename with date
            date_str = analysis.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
            filename = f"workout_analysis_{date_str}.json"
            filepath = output_dir / filename
            
            # Write analysis to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2)
            
            logger.info(f"Analysis saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return None

def get_api_key_from_config() -> Optional[str]:
    """
    Get OpenAI API key from config file.
    
    Returns:
        API key if found, None otherwise
    """
    config_path = Path.home() / '.garmin_openai_config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('api_key')
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error loading OpenAI API key from config: {e}")
    
    return None

def save_api_key_to_config(api_key: str) -> bool:
    """
    Save OpenAI API key to config file.
    
    Args:
        api_key: The OpenAI API key
        
    Returns:
        True if successful, False otherwise
    """
    config_path = Path.home() / '.garmin_openai_config.json'
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({'api_key': api_key}, f)
        return True
    except Exception as e:
        logger.error(f"Error saving API key to config file: {e}")
        return False
