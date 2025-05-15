# OpenAI Integration for Garmin Connect Data

This guide explains how to use the OpenAI integration to analyze your Garmin workout data.

## Overview

The OpenAI integration allows you to send your workout data to ChatGPT for personalized insights, analysis, and recommendations. The system:

1. Retrieves workout data from Garmin Connect
2. Formats the data for optimal analysis
3. Sends it to OpenAI's API
4. Returns personalized insights about your workout
5. Saves the analysis for future reference

## Requirements

- An OpenAI API key (available at [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys))
- Python 3.7 or higher
- The `openai` Python package (automatically installed with this project)

## Setup

1. Run the configuration command to set up your OpenAI API key:
   ```
   python analyze_workout.py --configure
   ```

2. Follow the prompts to enter your API key. The key will be stored securely in your home directory.

## Usage

### List Recent Activities

To list your recent activities without analyzing them:

```
python analyze_workout.py --list-activities
```

By default, this shows activities from the past 7 days. To change the number of days:

```
python analyze_workout.py --list-activities --days 14
```

### Analyze a Specific Activity

To analyze a specific activity, use its activity ID:

```
python analyze_workout.py --activity-id 12345678
```

You can find activity IDs by using the `--list-activities` command.

### Analyze Activities from a Specific Date

To analyze activities from a specific date:

```
python analyze_workout.py --date 2025-05-10
```

If multiple activities exist for that date, you'll be prompted to choose one.

## Analysis Output

The analysis results include:

- Overview of the workout
- Performance insights based on metrics
- Comparison to your previous performances (when available)
- Recovery recommendations
- Training suggestions

The analysis is displayed in the terminal and saved as a JSON file in the `exports/analysis` directory.

### AI Model Selection

The system automatically selects the best available OpenAI model from the following options:

1. GPT-4 Turbo (if available)
2. GPT-4 (if available)
3. GPT-3.5 Turbo (fallback option)

If none of the preferred models are available, the system will default to GPT-3.5 Turbo.

## Advanced Usage

### Programmatic Use

You can also use the OpenAI integration programmatically in your own Python scripts:

```python
from utils.openai_integration import OpenAIAnalyzer

# Initialize the analyzer
analyzer = OpenAIAnalyzer()

# Format your workout data
formatted_data = analyzer.format_workout_data(workout_data)

# Get analysis
analysis = analyzer.analyze_workout(formatted_data)

# Save the results
analyzer.save_analysis(analysis)
```

### Environment Variables

Instead of using the configuration command, you can set the `OPENAI_API_KEY` environment variable:

```
export OPENAI_API_KEY="your-api-key-here"
```

## Troubleshooting

- **API Key Issues**: Make sure your API key is valid and has not expired
- **Connection Problems**: Check your internet connection
- **Rate Limiting**: OpenAI has rate limits; if you hit them, wait and try again later
- **Missing Data**: Some workouts may not have enough data for meaningful analysis
- **Model Not Found**: If you encounter a "model not found" error, the system will automatically try to use an alternative model
- **API Errors**: Check the logs in the terminal for detailed error information

If you encounter persistent issues:

1. Run with `--configure` to update your API key
2. Check that your OpenAI account has access to the models being requested
3. Verify that your billing information is up to date on your OpenAI account

## Privacy Note

Your workout data is sent to OpenAI's API for analysis. OpenAI may store this data according to their privacy policy. Only send data you are comfortable sharing.
