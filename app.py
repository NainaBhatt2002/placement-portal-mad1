from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, Student, Company, PlacementDrive, Application
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

with app.app_context():
    setup_database()

@app.route('/')
def index():
    return redirect(url_for('login'))

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
                new_user = Student(name=name, email=email, password=hashed_password, contact='N/A')
            elif role == 'company':
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        
        # Check Admin
        admin = Admin.query.filter_by(username=username_or_email).first()
        if admin and (admin.password == password or check_password_hash(admin.password, password)):
            session['user_id'] = admin.id
            session['role'] = 'admin'
            return redirect(url_for('admin_dashboard'))
            
        # Check Student
        student = Student.query.filter(
            or_(
                Student.email == username_or_email,
                Student.name == username_or_email
            )
        ).first()
        if student and check_password_hash(student.password, password):
            if getattr(student, 'is_blacklisted', False):
                flash('Your account has been blacklisted. Please contact administration.', 'error')
                return redirect(url_for('login'))
            session['user_id'] = student.id
            session['role'] = 'student'
            return redirect(url_for('student_dashboard'))
            
        # 3. Check Company
        company = Company.query.filter(
            or_(
                Company.email == username_or_email,
                Company.name == username_or_email
            )
        ).first()
        if company and check_password_hash(company.password, password):
            if getattr(company, 'is_blacklisted', False):
                flash('Your account has been blacklisted. Please contact administration.', 'error')
                return redirect(url_for('login'))
            if not company.is_approved:
                flash('Your account is pending admin approval.', 'error')
                return redirect(url_for('login'))
            session['user_id'] = company.id
            session['role'] = 'company'
            return redirect(url_for('company_dashboard'))
            
        flash('Invalid credentials. Please try again.', 'error')
        return redirect(url_for('login'))
        
    return render_template('login.html')

# Admin routes

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

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    pending_companies = Company.query.filter_by(is_approved=False).all()
    pending_drives = PlacementDrive.query.filter_by(status='Pending').all()
    total_companies = Company.query.count()
    total_students = Student.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()
    return render_template('admin_dashboard.html', 
                            pending_companies=pending_companies,
                            pending_drives=pending_drives,
                            total_companies=total_companies,
                            total_students=total_students,
                            total_drives=total_drives,
                            total_applications=total_applications)

@app.route('/admin/reject_company/<int:company_id>', methods=['POST'])
def reject_company(company_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    company = Company.query.get_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    flash(f'Company "{company.name}" registration rejected.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_drive/<int:drive_id>', methods=['POST'])
def approve_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Approved'
    db.session.commit()
    flash(f'Job posting "{drive.job_title}" approved.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_drive/<int:drive_id>', methods=['POST'])
def reject_drive(drive_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = 'Rejected'
    db.session.commit()
    flash(f'Job posting "{drive.job_title}" rejected.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/students')
def manage_students():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    q = request.args.get('q', '')
    if q:
        students = Student.query.filter(
            or_(
                Student.name.ilike(f'%{q}%'),
                Student.email.ilike(f'%{q}%'),
                Student.contact.ilike(f'%{q}%')
            )
        ).all()
    else:
        students = Student.query.all()
    return render_template('admin_students.html', students=students, q=q)

@app.route('/admin/toggle_student_blacklist/<int:student_id>', methods=['POST'])
def toggle_student_blacklist(student_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = not student.is_blacklisted
    db.session.commit()
    return redirect(url_for('manage_students'))

@app.route('/admin/companies')
def manage_companies():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    q = request.args.get('q', '')
    if q:
        companies = Company.query.filter(
            or_(
                Company.name.ilike(f'%{q}%'),
                Company.industry.ilike(f'%{q}%')
            )
        ).all()
    else:
        companies = Company.query.all()
    return render_template('admin_companies.html', companies=companies, q=q)

@app.route('/admin/toggle_company_blacklist/<int:company_id>', methods=['POST'])
def toggle_company_blacklist(company_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    company = Company.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    db.session.commit()
    return redirect(url_for('manage_companies'))

@app.route('/admin/drives')
def manage_drives():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    drives = PlacementDrive.query.all()
    return render_template('admin_drives.html', drives=drives)

@app.route('/admin/applications')
def manage_applications():
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
    applications = Application.query.all()
    return render_template('admin_applications.html', applications=applications)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

#Student routes

@app.route('/student/dashboard')
def student_dashboard():
    if session.get('role') != 'student':
        flash('Unauthorized access or please log in.', 'error')
        return redirect(url_for('login'))
        
    student = Student.query.get(session.get('user_id'))
    if not student or student.is_blacklisted:
        session.clear()
        flash('Your account has been blacklisted or removed.', 'error')
        return redirect(url_for('login'))
        
    return render_template('student_dashboard.html')

#Company routes

@app.route('/company/dashboard')
def company_dashboard():
    if session.get('role') != 'company':
        flash('Unauthorized access or please log in.', 'error')
        return redirect(url_for('login'))
        
    company = Company.query.get(session.get('user_id'))
    if not company or company.is_blacklisted or not company.is_approved:
        session.clear()
        flash('Your account has been blacklisted, removed, or is no longer approved.', 'error')
        return redirect(url_for('login'))
        
    return render_template('company_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)