CAREERCONNECT - PLacement Portal Application (Modern Application Development I)

A comprehensive, full-stack web application built with Flask to streamline the recruitment and placement process for educational institutions. The platform facilitates seamless interaction between students, companies, and administrators, ensuring a transparent and efficient hiring workflow.

#KEY FEATURES

#FOR STUDENTS
Secure Authentication: Register and log in with email and password to access a personalized dashboard.

Profile Management: Maintain an up-to-date professional profile, including contact details, education history, and specialized skills.

Resume Management: Upload and update resumes in PDF format, which are then made available to potential employers.

Job Discovery: Browse and search active job postings using filters for company name, job title, or required skills.

Application Tracking: Apply to multiple jobs and monitor the real-time status of applications, from initial submission to final selection.

#FOR COMPANIES
Job Posting Management: Create, edit, and manage job drives with detailed descriptions, eligibility criteria, and application deadlines.

Applicant Review: Directly access student profiles and view uploaded resumes to identify the best talent for specific roles.

Hiring Pipeline: Update applicant statuses through various stages, including Shortlisted, Interview, Selected, or Rejected.

Company Profile: Manage public-facing information such as HR contact details, industry focus, and company website.

#FOR ADMINISTRATORS
System Oversight: Monitor global statistics including total students, registered companies, and overall application volume.

Approval Workflow: Maintain quality control by reviewing and approving new company registrations and job postings before they are visible to students.

Account Management: Search for specific users and manage their access by blacklisting or activating student and company accounts as needed.

Centralized Database: Access a global view of all placement drives and application histories across the entire system.

#TECH STACK
Backend: Python 3 with the Flask web framework.

Database: SQLite with SQLAlchemy ORM for efficient data modeling and queries.

Security: Password hashing via Werkzeug to ensure user data protection.

Authentication: Flask-Login for secure session management and role-based access control.

Frontend: Responsive UI built with HTML5, Custom CSS, and Bootstrap 5.

#PROJECT STRUCTURE
placement-portal-mad1-main/
├── app.py              #Core application logic, routes, and authentication
├── models.py           #SQLAlchemy database schema and relationships
├── requirements.txt    #List of required Python packages and versions
├── static/
│   └── styles.css      #Custom interface styling and layout rules
├── templates/          #Jinja2 HTML templates for all user roles
│   ├── admin_*.html    #Administrative management views
│   ├── company_*.html  #Employer-facing dashboards and forms
│   └── student_*.html  #Student interface and job search views
└── uploads/            #Secure storage directory for student resumes

#INSTALLATION & SETUP
1. Clone the Repository

git clone https://github.com/NainaBhatt2002/placement-portal-mad1.git
cd placement-portal-mad1

2. Initialize Virtual Environment

python -m venv venv

venv\Scripts\activate 

3. Install Dependencies

pip install -r requirements.txt

4. Run the Application

python app.py or flask run

The server will start at http://127.0.0.1:5000/. A default administrator account is automatically generated upon the first run for system setup:

#ADMIN DETAILS
Email: admin@admin.com
Username: admin
Password: adminpassword

#CONFIGURATION NOTE
File Uploads: The application is configured with a MAX_CONTENT_LENGTH of 5 MB for file uploads to maintain server performance.

Resume Format: To ensure consistency for recruiters, the system exclusively accepts PDF formats for student resumes.

#DEVELOPED BY:

Author: Naina Bhatt
Program: BS in Data Science and Applications
Institution: Indian Institute of Technology Madras (IITM)

This project was completed as part of the Modern Application Development 1 (MAD 1) course requirements.
