from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    user = db.relationship('User', backref=db.backref('admin_profile', uselist=False, cascade="all, delete-orphan"))

class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    user = db.relationship('User', backref=db.backref('company_profile', uselist=False, cascade="all, delete-orphan"))
    
    hr_contact = db.Column(db.String(50), nullable=False)
    industry = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(150), nullable=True)
    is_approved = db.Column(db.Boolean, default=False)
    is_blacklisted = db.Column(db.Boolean, default=False)

    drives = db.relationship('PlacementDrive', backref='company', lazy=True, cascade="all, delete-orphan")

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False, cascade="all, delete-orphan"))
    
    contact = db.Column(db.String(15), nullable=False)
    education = db.Column(db.Text, nullable=True)
    skills = db.Column(db.String(255), nullable=True)
    resume_path = db.Column(db.String(255), nullable=True)
    is_blacklisted = db.Column(db.Boolean, default=False)

    applications = db.relationship('Application', backref='student', lazy=True, cascade="all, delete-orphan")

class PlacementDrive(db.Model):
    """Also acts as the Job Position table"""
    __tablename__ = 'placement_drive'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    skills_required = db.Column(db.String(255), nullable=True)
    experience_required = db.Column(db.String(100), nullable=True)
    salary_range = db.Column(db.String(100), nullable=True)
    eligibility_criteria = db.Column(db.Text, nullable=True)
    application_deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='Pending')

    applications = db.relationship('Application', backref='drive', lazy=True, cascade="all, delete-orphan")

class Application(db.Model):
    __tablename__ = 'application'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Applied')
    
    placement = db.relationship('Placement', backref='application', uselist=False, cascade="all, delete-orphan")

class Placement(db.Model):
    """Records final job offerings linked directly to an application"""
    __tablename__ = 'placement'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), unique=True, nullable=False)
    offer_date = db.Column(db.DateTime, default=datetime.utcnow)
    offer_details = db.Column(db.Text, nullable=True)
