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

def initialize_database():
    """Initialize database tables and default data if they don't exist"""
    try:
        # Create tables if they don't exist
        create_tables()
        
        # Add default categories if they don't exist
        initialize_categories()
        
        # Add a test user if no users exist
        create_test_user()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

def create_tables():
    """Create database tables if they don't exist"""
    try:
        # You can use Supabase's SQL execution capability to create tables
        # This is typically done in the Supabase dashboard, but we can also do it here
        
        # Check if tables exist
        users_exist = supabase.table("users").select("count", count="exact").execute()
        categories_exist = supabase.table("categories").select("count", count="exact").execute()
        reminders_exist = supabase.table("reminders").select("count", count="exact").execute()
        places_exist = supabase.table("places").select("count", count="exact").execute()
        
        logger.info("Tables verified in Supabase")
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        # Tables might not exist yet, which would cause an error
        # We'd need to create them via SQL or the Supabase dashboard
        logger.error("Make sure tables are created in Supabase dashboard")
        raise

def initialize_categories():
    """Initialize default categories if they don't exist"""
    try:
        # Check if any categories exist
        response = supabase.table("categories").select("count", count="exact").execute()
        count = response.count if hasattr(response, 'count') else 0
        
        if count == 0:
            # Add default categories
            categories = [
                {"name": "Grocery", "google_places_type": "grocery_or_supermarket", "icon": "cart-shopping"},
                {"name": "Pharmacy", "google_places_type": "pharmacy", "icon": "prescription-bottle-medical"},
                {"name": "Shopping", "google_places_type": "shopping_mall", "icon": "bag-shopping"},
                {"name": "Restaurant", "google_places_type": "restaurant", "icon": "utensils"},
                {"name": "Convenience Store", "google_places_type": "convenience_store", "icon": "store"}
            ]
            
            for category in categories:
                supabase.table("categories").insert(category).execute()
                
            logger.info("Default categories created")
    except Exception as e:
        logger.error(f"Error initializing categories: {e}")
        raise

def create_test_user():
    """Create a test user if no users exist"""
    try:
        # Check if any users exist
        response = supabase.table("users").select("count", count="exact").execute()
        count = response.count if hasattr(response, 'count') else 0
        
        if count == 0:
            # Add test user
            test_user = {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": "test",  # In production, use proper password hashing
                "search_radius": 1000,
                "notification_enabled": True,
                "created_at": "now()"
            }
            
            supabase.table("users").insert(test_user).execute()
            logger.info("Test user created")
    except Exception as e:
        logger.error(f"Error creating test user: {e}")
        raise