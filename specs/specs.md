<!-- STACK_PROFILE: {"backend": "node/express", "frontend": "react", "database": "sqlite"} -->

**Specs for Dark App Factory**

**Architecture**

* Backend:
	+ Language: Node.js
	+ Framework: Express
	+ ORM: Sequelize
* Frontend:
	+ Framework: React 18 (with Vite and TypeScript)
	+ CSS Framework: Tailwind CSS
	+ Animation Library: Framer Motion
* Database: SQLite

**Core Data Models**

* **Patient**
	+ id (primary key, auto-incrementing integer)
	+ name (string)
	+ email (string, unique)
	+ phone (string)
	+ address (string)
	+ birthdate (date)
* **Dentist**
	+ id (primary key, auto-incrementing integer)
	+ name (string)
	+ email (string, unique)
	+ phone (string)
	+ address (string)
	+ professional_title (string)
* **Appointment**
	+ id (primary key, auto-incrementing integer)
	+ patient_id (foreign key referencing Patient.id)
	+ dentist_id (foreign key referencing Dentist.id)
	+ appointment_date (date)
	+ start_time (time)
	+ end_time (time)

**API Endpoints**

### Patients

* `GET /patients`: Retrieve list of patients
* `POST /patients`: Create new patient
* `GET /patients/{id}`: Retrieve single patient by ID
* `PUT /patients/{id}`: Update existing patient
* `DELETE /patients/{id}`: Delete patient

### Dentists

* `GET /dentists`: Retrieve list of dentists
* `POST /dentists`: Create new dentist
* `GET /dentists/{id}`: Retrieve single dentist by ID
* `PUT /dentists/{id}`: Update existing dentist
* `DELETE /dentists/{id}`: Delete dentist

### Appointments

* `GET /appointments`: Retrieve list of appointments
* `POST /appointments`: Create new appointment
* `GET /appointments/{id}`: Retrieve single appointment by ID
* `PUT /appointments/{id}`: Update existing appointment
* `DELETE /appointments/{id}`: Delete appointment

### Authentication

* `POST /login`: Authenticate user (email and password)
* `POST /register`: Register new user (email, password, name)

**State Machines**

* **Patient State Machine**
	+ Initial state: NEW
	+ Transitions:
		- From NEW to ENROLLED upon successful registration
		- From ENROLLED to APPOINTMENT_SCHEDULED upon scheduling appointment
		- From APPOINTMENT_SCHEDULED to APPOINTMENT_COMPLETED upon completion of appointment
* **Dentist State Machine**
	+ Initial state: AVAILABLE
	+ Transitions:
		- From AVAILABLE to BOOKED upon booking appointment
		- From BOOKED to UNAVAILABLE upon completing appointment

**Digital Twin Integration**

* Required for data exchange between patient and dentist systems
* To be implemented using GraphQL API

**Database Schema**

```sql
CREATE TABLE patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    address TEXT,
    birthdate DATE
);

CREATE TABLE dentists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    address TEXT,
    professional_title VARCHAR(100)
);

CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER REFERENCES patients(id),
    dentist_id INTEGER REFERENCES dentists(id),
    appointment_date DATE,
    start_time TIME,
    end_time TIME
);
```

**API Reference**

```markdown
## Patients API

### GET /patients

* Retrieves list of patients
* Response:
	+ 200 OK: JSON array of patient objects
	+ 401 Unauthorized: Authentication required

### POST /patients

* Creates new patient
* Request Body:
	+ name: string
	+ email: string (unique)
	+ phone: string
	+ address: string
	+ birthdate: date
* Response:
	+ 201 Created: JSON object of newly created patient
	+ 400 Bad Request: Invalid request data

### GET /patients/{id}

* Retrieves single patient by ID
* Path Parameters:
	+ id: integer (patient ID)
* Response:
	+ 200 OK: JSON object of patient
	+ 404 Not Found: Patient not found

### PUT /patients/{id}

* Updates existing patient
* Path Parameters:
	+ id: integer (patient ID)
* Request Body:
	+ name: string
	+ email: string (unique)
	+ phone: string
	+ address: string
	+ birthdate: date
* Response:
	+ 200 OK: JSON object of updated patient
	+ 400 Bad Request: Invalid request data

### DELETE /patients/{id}

* Deletes patient
* Path Parameters:
	+ id: integer (patient ID)
* Response:
	+ 204 No Content: Patient deleted
	+ 404 Not Found: Patient not found
```

**README.md Template**

```markdown
# Project Name

## Table of Contents

1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Setup](#setup)
4. [Running the Application](#running-the-application)
5. [API Documentation](#api-documentation)

## Introduction

This project is a dental clinic management system, developed using Node.js and React.

## Requirements

* Node.js 14 or higher
* npm 6 or higher
* SQLite 3 or higher

## Setup

1. Clone the repository: `git clone https://github.com/your-repo.git`
2. Install dependencies: `npm install`
3. Configure database connection: edit `config/database.js` file

## Running the Application

1. Start the server: `node index.js`
2. Open the application in your web browser: `http://localhost:3000`

## API Documentation

### Patients API

* Retrieves list of patients
* Response:
	+ 200 OK: JSON array of patient objects
	+ 401 Unauthorized: Authentication required

...

```

This output should cover all requirements specified, including rigorous and exhaustive specifications for the core data models, API endpoints, state machines, database schema, digital twin integration, and README template.