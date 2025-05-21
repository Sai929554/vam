import os
import logging
from app import app, db
import models

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import routes after models to avoid circular imports
import routes

# Initialize the database
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
        # Initialize database with sample data
        routes.initialize_database()
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run(host="0.0.0.0", port=5000, debug=True)
