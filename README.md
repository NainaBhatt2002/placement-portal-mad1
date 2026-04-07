# PLACEMENT PORTAL SYSTEM

A full-stack web application built using Flask that streamlines the placement process for students and administrators. The platform enables students to explore opportunities, apply for jobs, and track their application status, while providing administrators with tools to manage the entire workflow efficiently.

### FEATURES

### Student

* Register and log in securely
* Browse available job opportunities
* Apply to companies
* Track application status

### Admin

* Add, update, and delete job postings
* Manage student records
* View applications
* Oversee placement activities

## Tech Stack

* Backend: Flask (Python)
* Database: SQLite
* Frontend: HTML, CSS, Bootstrap
* ORM: SQLAlchemy

## Project Structure

placement-portal/
│── app.py
│── models.py
│── templates/
│── static/
│── instance/
│   └── placement.db
│── requirements.txt
│── README.md

## Installation and Setup

### 1. Clone the repository

git clone https://github.com/your-username/placement-portal.git
cd placement-portal

### 2. Create a virtual environment

python -m venv venv
source venv/bin/activate and On Windows: venv\Scripts\activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Run the application

python app.py or flask run

## Usage

Open your browser and go to: http://127.0.0.1:5000/ 

You can register as a student or log in as an administrator to begin using the platform.

## Screenshots

Include screenshots of key pages such as the login page, dashboard, and job listings.

## Future Improvements

* Implement secure password hashing
* Add email notifications
* Enable resume uploads
* Improve user interface and overall user experience

## Contributing

Contributions are welcome. You can fork the repository and submit a pull request with your changes.

## Author

Naina Bhatt
IIT Madras BS Degree Program
