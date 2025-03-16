"""
Supabase client utility for the application.
This module provides functions for interacting with the Supabase API.
"""
import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Cache the client to avoid creating multiple connections
_supabase_client = None

def get_supabase_client() -> Client:
    """
    Get a Supabase client instance.
    
    Returns:
        Client: A Supabase client instance.
    
    Raises:
        ValueError: If the Supabase URL or key is not set.
        Exception: If there is an error creating the client.
    """
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
    
    try:
        logger.debug("Creating Supabase client")
        _supabase_client = create_client(supabase_url, supabase_key)
        return _supabase_client
    except Exception as e:
        logger.error(f"Error creating Supabase client: {str(e)}")
        raise 