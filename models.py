from datetime import datetime
from app import db
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Float, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    search_radius = db.Column(db.Integer, default=1000)  # radius in meters
    notification_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"

class Category(db.Model):
    __tablename__ = "categories"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    google_places_type = db.Column(db.String(64), nullable=False)
    icon = db.Column(db.String(64), nullable=True)
    
    # Relationships
    reminders = relationship("Reminder", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.name}>"

class Reminder(db.Model):
    __tablename__ = "reminders"
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reminders")
    category = relationship("Category", back_populates="reminders")
    
    def __repr__(self):
        return f"<Reminder {self.title}>"

class Place(db.Model):
    __tablename__ = "places"
    
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.String(128), nullable=False, unique=True)
    name = db.Column(db.String(128), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(256), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    category = relationship("Category")
    
    def __repr__(self):
        return f"<Place {self.name}>"

class NotificationHistory(db.Model):
    __tablename__ = "notification_history"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reminder_id = db.Column(db.Integer, db.ForeignKey("reminders.id"), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey("places.id"), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    reminder = relationship("Reminder")
    place = relationship("Place")
    
    def __repr__(self):
        return f"<Notification for {self.reminder_id} at {self.sent_at}>"
