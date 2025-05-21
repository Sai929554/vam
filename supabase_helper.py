import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    logger.error("Supabase URL or key not found in environment variables")
    raise ValueError("Supabase URL or key not found in environment variables")

try:
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Supabase client: {e}")
    raise

# Helper functions to work with Supabase

def get_user_by_username(username):
    """Get a user by username"""
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        data = response.data
        return data[0] if data else None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None

def get_reminders_by_user_id(user_id, completed=None):
    """Get reminders for a user"""
    try:
        query = supabase.table("reminders").select("*").eq("user_id", user_id)
        
        if completed is not None:
            query = query.eq("completed", completed)
            
        response = query.execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting reminders: {e}")
        return []

def get_categories():
    """Get all categories"""
    try:
        response = supabase.table("categories").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return []

def get_category_by_id(category_id):
    """Get a category by ID"""
    try:
        response = supabase.table("categories").select("*").eq("id", category_id).execute()
        data = response.data
        return data[0] if data else None
    except Exception as e:
        logger.error(f"Error getting category: {e}")
        return None

def create_reminder(user_id, title, category_id, description=""):
    """Create a new reminder"""
    try:
        reminder_data = {
            "user_id": user_id,
            "title": title,
            "description": description,
            "category_id": category_id,
            "completed": False,
            "created_at": "now()"
        }
        
        response = supabase.table("reminders").insert(reminder_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        return None

def update_reminder(reminder_id, data):
    """Update a reminder"""
    try:
        response = supabase.table("reminders").update(data).eq("id", reminder_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error updating reminder: {e}")
        return None

def delete_reminder(reminder_id):
    """Delete a reminder"""
    try:
        response = supabase.table("reminders").delete().eq("id", reminder_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error deleting reminder: {e}")
        return False

def update_user_settings(user_id, settings):
    """Update user settings"""
    try:
        response = supabase.table("users").update(settings).eq("id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        return None

def save_place(place_data):
    """Save a place to the database"""
    try:
        # Check if place already exists
        response = supabase.table("places").select("*").eq("place_id", place_data["place_id"]).execute()
        
        if response.data:
            # Update existing place
            place_id = response.data[0]["id"]
            response = supabase.table("places").update(place_data).eq("id", place_id).execute()
            return response.data[0] if response.data else None
        else:
            # Create new place
            response = supabase.table("places").insert(place_data).execute()
            return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error saving place: {e}")
        return None

def record_notification(user_id, reminder_id, place_id):
    """Record a notification in history"""
    try:
        notification_data = {
            "user_id": user_id,
            "reminder_id": reminder_id,
            "place_id": place_id,
            "sent_at": "now()"
        }
        
        response = supabase.table("notification_history").insert(notification_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error recording notification: {e}")
        return None