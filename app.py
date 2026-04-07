from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, Student, Company
import os
from sqlalchemy import or_

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

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        
        # 1. Check Admin (handles plaintext password if it hasn't been re-seeded as a hash)
        admin = Admin.query.filter_by(username=username_or_email).first()
        if admin and (admin.password == password or check_password_hash(admin.password, password)):
            session['user_id'] = admin.id
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
            
        # 2. Check Student
        student = Student.query.filter(
            or_(
                Student.email == username_or_email,
                Student.name == username_or_email
            )
        ).first()
        if student and check_password_hash(student.password, password):
            session['user_id'] = student.id
            session['role'] = 'student'
            return redirect(url_for('student_dashboard'))
            
        # 3. Check Company
        company = Company.query.filter_by(email=username_or_email).first()
        if company and check_password_hash(company.password, password):
            if not company.is_approved:
                flash('Your account is pending admin approval.', 'error')
                return redirect(url_for('login'))
            session['user_id'] = company.id
            session['role'] = 'company'
            return redirect(url_for('company_dashboard'))
            
        flash('Invalid credentials. Please try again.', 'error')
        return redirect(url_for('login'))
        
    return render_template('login.html')

@app.route('/admin/approve_company/<int:company_id>', methods=['POST'])
def approve_company(company_id):
    if session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('login'))
    
    company = Company.query.get_or_404(company_id)
    
    company.is_approved = True
    db.session.commit()
        
    flash(f'Company "{company.name}" has been approved successfully!.', 'success')
    return redirect(url_for('admin_dashboard'))

# Placeholder dashboard routes (to prevent redirect errors upon successful login)
@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    pending_companies = Company.query.filter_by(is_approved=False).all()
    return render_template('admin_dashboard.html', pending_companies=pending_companies)

@app.route('/student/dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/company/dashboard')
def company_dashboard():
    return render_template('company_dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not role or not name or not email or not password:
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        
        try:
            if role == 'student':
                # Use default value for contact since it is required in model but missing from UI form
                new_user = Student(name=name, email=email, password=hashed_password, contact='N/A')
            elif role == 'company':
                # Use default value for HR contact
                new_user = Company(name=name, email=email, password=hashed_password, hr_contact='N/A')
            else:
                flash('Invalid role selected!', 'error')
                return redirect(url_for('register'))
                
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Email already registered or an error occurred.', 'error')
            return redirect(url_for('register'))
            
    return render_template('register.html')

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)