# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View current school announcements
- Manage dated announcements while signed in as a teacher

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/announcements`                                                  | Get announcements active on the current date                        |
| POST   | `/announcements`                                                  | Create an announcement (authentication required)                    |
| PUT    | `/announcements/{id}`                                             | Modify an announcement (authentication required)                    |
| DELETE | `/announcements/{id}`                                             | Delete an announcement (authentication required)                    |

Authenticated announcement requests use the `Authorization: Bearer <session_token>`
header returned by `/auth/login`. An authenticated `GET /announcements` returns all
announcements, including scheduled and expired records. Announcement request bodies
contain a `message`, optional `start_date`, and required `expiration_date`; dates use
the `YYYY-MM-DD` format.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Announcements** - Uses a database-generated identifier:

   - Message
   - Optional start date
   - Required expiration date

All data is stored in MongoDB.
