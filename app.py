from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, Admin
import os

app = Flask(__name__)

#config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ourlittlesecret'

# Initialize the db
db.init_app(app)

def setup_database():
    with app.app_context():
        # Create all tables programmatically
        db.create_all()
        
        # Creating Admin 
        admin_exists = Admin.query.filter_by(username='admin').first()
        if not admin_exists:
            default_admin = Admin(username='admin', password= generate_password_hash('adminpassword'))
            db.session.add(default_admin)
            db.session.commit()
            print("Database initialized and predefined Admin seeded successfully.")
        else:
            print("Database is already initialized.")

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)
