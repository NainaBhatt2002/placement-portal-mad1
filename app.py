from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Admin, Student, Company, PlacementDrive, Application
import os
import uuid
from sqlalchemy import or_
from datetime import datetime

app = Flask(__name__)

#config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ourlittlesecret'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads', 'resumes')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # 5 MB limit

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
                resume_file = request.files.get('resume')
                resume_filename = None
                if resume_file and resume_file.filename != '':
                    if resume_file.filename.lower().endswith('.pdf'):
                        original_filename = secure_filename(resume_file.filename)
                        resume_filename = f"{uuid.uuid4().hex}_{original_filename}"
                        resume_file.save(os.path.join(app.config['UPLOAD_FOLDER'], resume_filename))
                    else:
                        flash('Invalid file format. Only PDF allowed.', 'error')
                        return redirect(url_for('register'))

                new_user = Student(name=name, email=email, password=hashed_password, contact='N/A', resume_path=resume_filename)
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
    drive.status = 'Active'
    db.session.commit()
    flash(f'Job posting "{drive.job_title}" activated.', 'success')
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
        
    applications = Application.query.filter_by(student_id=student.id).all()
    total_applications = len(applications)
    shortlisted = sum(1 for a in applications if a.status == 'Shortlisted')
    selected = sum(1 for a in applications if a.status == 'Selected')
    rejected = sum(1 for a in applications if a.status == 'Rejected')
    
    recent_applications = Application.query.filter_by(student_id=student.id).order_by(Application.application_date.desc()).limit(5).all()
        
    return render_template('student_dashboard.html', student=student, total_applications=total_applications, 
                           shortlisted=shortlisted, selected=selected, rejected=rejected, 
                           recent_applications=recent_applications)

@app.route('/student/profile', methods=['GET', 'POST'])
def student_profile():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
        
    student = Student.query.get(session.get('user_id'))
    if request.method == 'POST':
        student.contact = request.form.get('contact')
        student.education = request.form.get('education')
        student.skills = request.form.get('skills')
        
        resume_file = request.files.get('resume')
        if resume_file and resume_file.filename != '':
            if resume_file.filename.lower().endswith('.pdf'):
                original_filename = secure_filename(resume_file.filename)
                resume_filename = f"{uuid.uuid4().hex}_{original_filename}"
                resume_file.save(os.path.join(app.config['UPLOAD_FOLDER'], resume_filename))
                # Optional: remove old resume if it exists
                if student.resume_path:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], student.resume_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                student.resume_path = resume_filename
            else:
                flash('Invalid file format. Only PDF allowed.', 'error')
                return redirect(url_for('student_profile'))
                
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student_profile'))
        
    return render_template('student_profile.html', student=student)

@app.route('/student/jobs')
def student_jobs():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    q = request.args.get('q', '')
    query = PlacementDrive.query.filter_by(status='Active')
    if q:
        query = query.join(Company).filter(
            or_(
                PlacementDrive.job_title.ilike(f'%{q}%'),
                PlacementDrive.skills_required.ilike(f'%{q}%'),
                Company.name.ilike(f'%{q}%')
            )
        )
    drives = query.all()
    
    # Get IDs of drives student has already applied to
    student_id = session.get('user_id')
    applied_drive_ids = [a.drive_id for a in Application.query.filter_by(student_id=student_id).all()]
    
    return render_template('student_jobs.html', drives=drives, applied_drive_ids=applied_drive_ids, q=q)

@app.route('/student/apply/<int:drive_id>', methods=['POST'])
def student_apply(drive_id):
    if session.get('role') != 'student':
        return redirect(url_for('login'))
        
    student = Student.query.get(session.get('user_id'))
    if not student.resume_path:
        flash('Please update your profile and upload a resume before applying.', 'error')
        return redirect(url_for('student_profile'))
        
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != 'Active':
        flash('Job posting is no longer active.', 'error')
        return redirect(url_for('student_jobs'))
        
    existing_app = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
    if existing_app:
        flash('You have already applied for this job.', 'error')
        return redirect(url_for('student_jobs'))
        
    application = Application(student_id=student.id, drive_id=drive.id)
    db.session.add(application)
    db.session.commit()
    
    flash('Application submitted successfully!', 'success')
    return redirect(url_for('student_applications'))

@app.route('/student/applications')
def student_applications():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
        
    applications = Application.query.filter_by(student_id=session.get('user_id')).order_by(Application.application_date.desc()).all()
    return render_template('student_applications.html', applications=applications)

@app.route('/uploads/resumes/<filename>')
def serve_resume(filename):
    if session.get('role') not in ['student', 'company', 'admin']:
        return redirect(url_for('login'))
    
    # We could add more strict access control (e.g. only company can view if student applied), 
    # but for now restrict to logged-in users only.
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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
        
    drives = PlacementDrive.query.filter_by(company_id=company.id).order_by(PlacementDrive.id.desc()).all()
    total_drives = len(drives)
    active_drives = sum(1 for d in drives if d.status == 'Active')
    
    drive_ids = [d.id for d in drives]
    applications = Application.query.filter(Application.drive_id.in_(drive_ids)).all() if drive_ids else []
    total_applications = len(applications)
    shortlisted = sum(1 for a in applications if a.status == 'Shortlisted')
    selected = sum(1 for a in applications if a.status == 'Selected')
        
    return render_template('company_dashboard.html',
        company=company,
        drives=drives,
        total_drives=total_drives,
        active_drives=active_drives,
        total_applications=total_applications,
        shortlisted=shortlisted,
        selected=selected
    )

@app.route('/company/drive/new', methods=['GET', 'POST'])
def company_post_drive():
    if session.get('role') != 'company':
        return redirect(url_for('login'))
        
    company = Company.query.get(session.get('user_id'))
    if not company or not company.is_approved:
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        job_title = request.form.get('job_title')
        job_description = request.form.get('job_description')
        skills_required = request.form.get('skills_required')
        experience_required = request.form.get('experience_required')
        salary_range = request.form.get('salary_range')
        eligibility_criteria = request.form.get('eligibility_criteria')
        deadline_str = request.form.get('application_deadline')
        
        # Validations
        if not job_title or not job_description or not deadline_str:
            flash('Required fields are missing.', 'error')
            return redirect(url_for('company_post_drive'))
            
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('company_post_drive'))
            
        new_drive = PlacementDrive(
            company_id=company.id,
            job_title=job_title,
            job_description=job_description,
            skills_required=skills_required,
            experience_required=experience_required,
            salary_range=salary_range,
            eligibility_criteria=eligibility_criteria,
            application_deadline=deadline,
            status='Pending'
        )
        db.session.add(new_drive)
        db.session.commit()
        flash('Job position created successfully. It is now pending admin approval.', 'success')
        return redirect(url_for('company_dashboard'))
        
    return render_template('company_post_drive.html')

@app.route('/company/drive/<int:drive_id>/status', methods=['POST'])
def company_update_drive_status(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != session.get('user_id'):
        flash('Unauthorized access.', 'error')
        return redirect(url_for('company_dashboard'))
        
    new_status = request.form.get('status')
    if new_status in ['Active', 'Closed']:
        drive.status = new_status
        db.session.commit()
        flash('Job posting status updated.', 'success')
    return redirect(url_for('company_dashboard'))

@app.route('/company/drive/<int:drive_id>/applications')
def company_drive_applications(drive_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != session.get('user_id'):
        flash('Unauthorized access.', 'error')
        return redirect(url_for('company_dashboard'))
        
    applications = Application.query.filter_by(drive_id=drive.id).all()
    return render_template('company_drive_applications.html', drive=drive, applications=applications)

@app.route('/company/application/<int:app_id>/status', methods=['POST'])
def company_update_app_status(app_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    application = Application.query.get_or_404(app_id)
    if application.drive.company_id != session.get('user_id'):
        flash('Unauthorized access.', 'error')
        return redirect(url_for('company_dashboard'))
        
    new_status = request.form.get('status')
    if new_status in ['Shortlisted', 'Selected', 'Rejected', 'Applied']:
        application.status = new_status
        db.session.commit()
        flash(f'Application status updated to {new_status}.', 'success')
    return redirect(url_for('company_drive_applications', drive_id=application.drive_id))

@app.route('/company/student/<int:student_id>')
def company_student_profile(student_id):
    if session.get('role') != 'company':
        return redirect(url_for('login'))
    student = Student.query.get_or_404(student_id)
    return render_template('company_student_profile.html', student=student)

if __name__ == '__main__':
    app.run(debug=True)