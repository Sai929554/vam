import json
import logging
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from sqlalchemy.exc import SQLAlchemyError
from app import app, db
from models import User, Category, Reminder, Place, NotificationHistory
from services.google_places import get_nearby_places
from services.location_service import calculate_distance
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize database with categories and test user
def initialize_database():
    initialize_categories()
    create_test_user()

def initialize_categories():
    try:
        if db.session.query(Category).count() == 0:
            # Create category objects
            grocery = Category()
            grocery.name = "Grocery"
            grocery.google_places_type = "grocery_or_supermarket"
            grocery.icon = "cart-shopping"
            
            pharmacy = Category()
            pharmacy.name = "Pharmacy"
            pharmacy.google_places_type = "pharmacy"
            pharmacy.icon = "prescription-bottle-medical"
            
            shopping = Category()
            shopping.name = "Shopping"
            shopping.google_places_type = "shopping_mall"
            shopping.icon = "bag-shopping"
            
            restaurant = Category()
            restaurant.name = "Restaurant"
            restaurant.google_places_type = "restaurant"
            restaurant.icon = "utensils"
            
            convenience = Category()
            convenience.name = "Convenience Store"
            convenience.google_places_type = "convenience_store"
            convenience.icon = "store"
            
            # Add categories to session
            db.session.add_all([grocery, pharmacy, shopping, restaurant, convenience])
            db.session.commit()
            logger.info("Default categories created")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing categories: {e}")
        db.session.rollback()

# Create a test user if no users exist
def create_test_user():
    try:
        if db.session.query(User).count() == 0:
            test_user = User()
            test_user.username = "testuser"
            test_user.email = "test@example.com"
            test_user.password_hash = "test"  # In production, use werkzeug.security.generate_password_hash
            test_user.search_radius = 1000
            test_user.notification_enabled = True
            
            db.session.add(test_user)
            db.session.commit()
            logger.info("Test user created")
    except SQLAlchemyError as e:
        logger.error(f"Error creating test user: {e}")
        db.session.rollback()

# Home page
@app.route('/')
def index():
    # For simplicity, use the test user
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return render_template('index.html', error="User not found")
    
    reminders = db.session.query(Reminder).filter_by(user_id=user.id, completed=False).all()
    categories = db.session.query(Category).all()
    
    return render_template('index.html', 
                           user=user,
                           reminders=reminders,
                           categories=categories)

# Reminders page
@app.route('/reminders')
def reminder_list():
    user = db.session.query(User).filter_by(username="testuser").first()
    reminders = db.session.query(Reminder).filter_by(user_id=user.id).all()
    categories = db.session.query(Category).all()
    
    return render_template('reminders.html',
                           user=user,
                           reminders=reminders,
                           categories=categories)

# Settings page
@app.route('/settings')
def settings():
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return render_template('settings.html', error="User not found")
    return render_template('settings.html', user=user)

# API Routes
@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    reminders = db.session.query(Reminder).filter_by(user_id=user.id).all()
    reminder_list = []
    
    for reminder in reminders:
        reminder_list.append({
            "id": reminder.id,
            "title": reminder.title,
            "description": reminder.description,
            "category_id": reminder.category_id,
            "category_name": reminder.category.name,
            "completed": reminder.completed,
            "created_at": reminder.created_at.isoformat()
        })
    
    return jsonify({"reminders": reminder_list})

@app.route('/api/reminders', methods=['POST'])
def create_reminder():
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    
    if not data or 'title' not in data or 'category_id' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        new_reminder = Reminder(
            title=data['title'],
            description=data.get('description', ''),
            user_id=user.id,
            category_id=data['category_id']
        )
        
        db.session.add(new_reminder)
        db.session.commit()
        
        return jsonify({
            "message": "Reminder created successfully",
            "reminder": {
                "id": new_reminder.id,
                "title": new_reminder.title,
                "description": new_reminder.description,
                "category_id": new_reminder.category_id,
                "category_name": new_reminder.category.name,
                "completed": new_reminder.completed,
                "created_at": new_reminder.created_at.isoformat()
            }
        }), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error creating reminder: {e}")
        return jsonify({"error": "Failed to create reminder"}), 500

@app.route('/api/reminders/<int:reminder_id>', methods=['PUT'])
def update_reminder(reminder_id):
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    reminder = db.session.query(Reminder).filter_by(id=reminder_id, user_id=user.id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    data = request.json
    
    try:
        if 'title' in data:
            reminder.title = data['title']
        if 'description' in data:
            reminder.description = data['description']
        if 'category_id' in data:
            reminder.category_id = data['category_id']
        if 'completed' in data:
            reminder.completed = data['completed']
        
        db.session.commit()
        
        return jsonify({
            "message": "Reminder updated successfully",
            "reminder": {
                "id": reminder.id,
                "title": reminder.title,
                "description": reminder.description,
                "category_id": reminder.category_id,
                "category_name": reminder.category.name,
                "completed": reminder.completed,
                "created_at": reminder.created_at.isoformat()
            }
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error updating reminder: {e}")
        return jsonify({"error": "Failed to update reminder"}), 500

@app.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    reminder = db.session.query(Reminder).filter_by(id=reminder_id, user_id=user.id).first()
    if not reminder:
        return jsonify({"error": "Reminder not found"}), 404
    
    try:
        # First delete any notification history associated with this reminder
        notifications = db.session.query(NotificationHistory).filter_by(reminder_id=reminder_id).all()
        for notification in notifications:
            db.session.delete(notification)
        
        # Then delete the reminder
        db.session.delete(reminder)
        db.session.commit()
        
        return jsonify({"message": "Reminder deleted successfully"})
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error deleting reminder: {e}")
        return jsonify({"error": "Failed to delete reminder"}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = db.session.query(Category).all()
    category_list = []
    
    for category in categories:
        category_list.append({
            "id": category.id,
            "name": category.name,
            "google_places_type": category.google_places_type,
            "icon": category.icon
        })
    
    return jsonify({"categories": category_list})

@app.route('/api/settings', methods=['GET'])
def get_settings():
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "user_id": user.id,
        "search_radius": user.search_radius,
        "notification_enabled": user.notification_enabled
    })

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    
    try:
        if 'search_radius' in data:
            user.search_radius = data['search_radius']
        if 'notification_enabled' in data:
            user.notification_enabled = data['notification_enabled']
        
        db.session.commit()
        
        return jsonify({
            "message": "Settings updated successfully",
            "settings": {
                "user_id": user.id,
                "search_radius": user.search_radius,
                "notification_enabled": user.notification_enabled
            }
        })
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error updating settings: {e}")
        return jsonify({"error": "Failed to update settings"}), 500

@app.route('/api/nearby_places', methods=['POST'])
def find_nearby_places():
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    
    if not data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({"error": "Missing location data"}), 400
    
    latitude = data['latitude']
    longitude = data['longitude']
    
    # Get active reminders for the user
    reminders = db.session.query(Reminder).filter_by(user_id=user.id, completed=False).all()
    
    if not reminders:
        return jsonify({"places": [], "reminders": []})
    
    # Get unique categories from active reminders
    category_ids = set(reminder.category_id for reminder in reminders)
    categories = db.session.query(Category).filter(Category.id.in_(category_ids)).all()
    
    # Get nearby places from Google Places API
    nearby_places = []
    relevant_reminders = []
    
    for category in categories:
        try:
            places = get_nearby_places(
                latitude, 
                longitude, 
                user.search_radius, 
                category.google_places_type
            )
            
            for place in places:
                # Save the place to our database if not already exists
                existing_place = db.session.query(Place).filter_by(place_id=place['place_id']).first()
                
                if not existing_place:
                    new_place = Place(
                        place_id=place['place_id'],
                        name=place['name'],
                        category_id=category.id,
                        latitude=place['geometry']['location']['lat'],
                        longitude=place['geometry']['location']['lng'],
                        address=place.get('vicinity', '')
                    )
                    db.session.add(new_place)
                    db.session.commit()
                    place_db_id = new_place.id
                else:
                    place_db_id = existing_place.id
                
                # Find relevant reminders
                category_reminders = [r for r in reminders if r.category_id == category.id]
                
                for reminder in category_reminders:
                    if reminder not in relevant_reminders:
                        relevant_reminders.append(reminder)
                
                nearby_places.append({
                    "id": place_db_id,
                    "place_id": place['place_id'],
                    "name": place['name'],
                    "category_id": category.id,
                    "category_name": category.name,
                    "latitude": place['geometry']['location']['lat'],
                    "longitude": place['geometry']['location']['lng'],
                    "address": place.get('vicinity', ''),
                    "distance": calculate_distance(
                        latitude, 
                        longitude, 
                        place['geometry']['location']['lat'], 
                        place['geometry']['location']['lng']
                    )
                })
        
        except Exception as e:
            logger.error(f"Error fetching nearby places for category {category.name}: {e}")
    
    # Format reminders for response
    reminder_list = []
    for reminder in relevant_reminders:
        reminder_list.append({
            "id": reminder.id,
            "title": reminder.title,
            "description": reminder.description,
            "category_id": reminder.category_id,
            "category_name": reminder.category.name
        })
    
    # Sort places by distance
    nearby_places.sort(key=lambda x: x['distance'])
    
    return jsonify({
        "places": nearby_places,
        "reminders": reminder_list
    })

@app.route('/api/record_notification', methods=['POST'])
def record_notification():
    user = db.session.query(User).filter_by(username="testuser").first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    
    if not data or 'reminder_id' not in data or 'place_id' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        notification = NotificationHistory(
            user_id=user.id,
            reminder_id=data['reminder_id'],
            place_id=data['place_id']
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({"message": "Notification recorded successfully"}), 201
    
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error recording notification: {e}")
        return jsonify({"error": "Failed to record notification"}), 500
