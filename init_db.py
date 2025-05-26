from app import app, db
from models import User, Task, Category, Priority

if __name__ == '__main__':
    with app.app_context():
        print("Initializing database...")
        # Drop all existing tables
        db.drop_all()
        # Create tables
        db.create_all()
        print("Database initialized successfully!")
