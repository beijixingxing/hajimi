import os

# Default password if not set in environment
DEFAULT_PASSWORD = "123"

# Get password from environment variable or use default
API_KEY = os.environ.get("PASSWORD", DEFAULT_PASSWORD)

# Function to validate API key
def validate_api_key(api_key: str) -> bool:
    """
    Validate the provided API key against the configured key
    
    Args:
        api_key: The API key to validate
        
    Returns:
        bool: True if the key is valid, False otherwise
    """
    if not API_KEY:
        # If no API key is configured, authentication is disabled
        return True
    
    return api_key == API_KEY