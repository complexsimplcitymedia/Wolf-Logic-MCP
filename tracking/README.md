# Job Application Tracking System

A complete database and CLI tool for managing and tracking job applications, communications, and interview progress.

## Overview

This system provides:
- PostgreSQL database schema for storing application data
- Python API (`application_tracker.py`) for programmatic access
- Interactive CLI dashboard (`job_cli.py`) for daily usage
- Comprehensive tracking of emails, calls, responses, and interviews

## Architecture

### Database: PostgreSQL (wolf_logic @ 100.110.82.181:5433)

**Tables:**
- `job_applications` - Main application records with all tracking fields
- `application_history` - Audit log of all actions on applications

**Key Fields:**
- Application info: company_name, position_title, job_url, resume_version
- Communication: email_sent, call_made, call_date, call_duration
- Response tracking: response_received, response_type, response_date
- Interview: interview_scheduled, interview_date
- Metadata: date_applied, created_at, updated_at, notes

## Quick Start

### Environment Setup

```bash
source ~/anaconda3/bin/activate messiah
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/tracking
```

### Dashboard

View all statistics and action items:
```bash
python job_cli.py dashboard
```

### Add Application

```bash
python job_cli.py add-app "Google" "Software Engineer" "https://careers.google.com/..." "v1.0"
```

### Mark Actions

Mark email sent:
```bash
python job_cli.py mark-email 1 "/path/to/resume.pdf"
```

Mark call made (300 seconds):
```bash
python job_cli.py mark-call 1 300 "Great discussion about role"
```

Mark response received:
```bash
python job_cli.py mark-response 1 callback "Recruiter wants technical interview"
```

Schedule interview:
```bash
python job_cli.py mark-interview 1 "2025-12-10T14:00:00" "Technical interview with hiring manager"
```

### View Applications

Show pending follow-up calls:
```bash
python job_cli.py pending-calls 7
```

Show applications awaiting response:
```bash
python job_cli.py pending-responses
```

Show upcoming interviews:
```bash
python job_cli.py upcoming-interviews
```

List all applications:
```bash
python job_cli.py list 20
```

Get detailed view of single application:
```bash
python job_cli.py details 1
```

Search applications:
```bash
python job_cli.py search company "Google"
python job_cli.py search position "Engineer"
```

## Python API Usage

### Basic Usage

```python
from application_tracker import ApplicationTracker

tracker = ApplicationTracker()

# Add application
app_id = tracker.add_application(
    company="Google",
    position="Software Engineer",
    job_url="https://careers.google.com/...",
    resume_version="v1.0"
)

# Mark email sent
tracker.mark_email_sent(app_id, resume_path="/path/to/resume.pdf")

# Mark call made
tracker.mark_call_made(app_id, duration=300, notes="Great discussion")

# Mark response
tracker.mark_response(app_id, "callback", "Recruiter wants interview")

# Get statistics
stats = tracker.get_statistics()
print(f"Total apps: {stats['total_applications']}")
print(f"Responses: {stats['responses_received']}")
print(f"Response types: {stats['response_types']}")

# Get pending items
pending_calls = tracker.get_pending_calls(days=7)
pending_responses = tracker.get_pending_responses()
upcoming_interviews = tracker.get_interviews_upcoming()

# Get application details
app = tracker.get_application(app_id)

# Search
results = tracker.search_applications(company="Google")

tracker.close()
```

## API Functions

### Core Functions

**add_application(company, position, job_url=None, resume_version=None) -> int**
- Adds new application to database
- Returns: Application ID

**mark_email_sent(application_id, resume_path=None) -> bool**
- Marks email as sent for application
- Optional: resume file path

**mark_call_made(application_id, duration=None, notes=None) -> bool**
- Marks call as made
- Optional: duration (seconds) and notes

**mark_response(application_id, response_type, notes=None) -> bool**
- Records response from employer
- response_type: "rejection", "callback", "interview", etc.

**schedule_interview(application_id, interview_date=None, notes=None) -> bool**
- Schedules interview
- Optional: datetime and notes

### Query Functions

**get_statistics() -> Dict**
- Returns: total_applications, emails_sent, calls_made, responses_received, interviews_scheduled, avg_call_duration, response_types

**get_pending_calls(days=7) -> List[Dict]**
- Returns applications without calls in past N days

**get_pending_responses() -> List[Dict]**
- Returns applications awaiting response after email/call

**get_interviews_upcoming() -> List[Dict]**
- Returns scheduled interviews in future

**get_all_applications(limit=None, order_by="date_applied DESC") -> List[Dict]**
- Returns all applications with optional limit and ordering

**search_applications(company=None, position=None) -> List[Dict]**
- Search by company name or position title (partial match)

**get_application(application_id) -> Optional[Dict]**
- Get single application details

## CLI Commands Reference

### Reporting
- `dashboard` - Main dashboard with stats and action items
- `pending-calls [days]` - Show apps needing follow-up (default: 7 days)
- `pending-responses` - Show apps awaiting employer response
- `upcoming-interviews` - Show scheduled interviews
- `list [limit]` - List all applications (default: 20)
- `details <app_id>` - Show detailed application info
- `search <type> <term>` - Search by "company" or "position"

### Adding Data
- `add-app <company> <position> [url] [resume]` - Add new application

### Marking Actions
- `mark-email <app_id> [resume_path]` - Mark email as sent
- `mark-call <app_id> [duration] [notes]` - Mark call as made
- `mark-response <app_id> <type> [notes]` - Mark response received
- `mark-interview <app_id> [date] [notes]` - Schedule interview

## Database Schema Details

### job_applications Table

```sql
id                   SERIAL PRIMARY KEY
company_name         VARCHAR(255) NOT NULL
position_title       VARCHAR(255) NOT NULL
job_url              TEXT
resume_version       VARCHAR(50)
date_applied         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
email_sent           BOOLEAN DEFAULT FALSE
email_sent_date      TIMESTAMP
call_made            BOOLEAN DEFAULT FALSE
call_date            TIMESTAMP
call_duration        INTEGER (seconds)
response_received    BOOLEAN DEFAULT FALSE
response_type        VARCHAR(50)
response_date        TIMESTAMP
interview_scheduled  BOOLEAN DEFAULT FALSE
interview_date       TIMESTAMP
notes                TEXT
created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

### Indexes

- `idx_applications_company` - For fast company searches
- `idx_applications_position` - For fast position searches
- `idx_applications_date_applied` - For chronological queries
- `idx_applications_call_made` - For pending call queries
- `idx_applications_response` - For response tracking
- `idx_applications_interview` - For interview queries

### application_history Table

```sql
id              SERIAL PRIMARY KEY
application_id  INTEGER FOREIGN KEY -> job_applications(id)
action          VARCHAR(100)
details         TEXT
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

Audit log of all actions. Examples:
- APPLICATION_ADDED
- EMAIL_SENT
- CALL_MADE
- RESPONSE_RECEIVED
- INTERVIEW_SCHEDULED

## Examples

### Complete Workflow

```bash
# Add application
python job_cli.py add-app "Google" "Senior Engineer" "https://careers.google.com/job"

# Mark email sent (with resume)
python job_cli.py mark-email 1 "~/resume_2024.pdf"

# Wait for response...

# Mark call made
python job_cli.py mark-call 1 420 "Phone interview with recruiter"

# After call, get response
python job_cli.py mark-response 1 callback "Wants to schedule technical interview"

# Schedule interview
python job_cli.py mark-interview 1 "2025-12-15T14:00:00" "Technical interview - 2 hours"

# Check dashboard
python job_cli.py dashboard

# View application details
python job_cli.py details 1
```

### Reporting

```bash
# What applications need follow-up?
python job_cli.py pending-calls 3

# Which companies haven't responded?
python job_cli.py pending-responses

# What's coming up?
python job_cli.py upcoming-interviews

# How am I doing overall?
python job_cli.py dashboard
```

## Database Connection

**Host:** 100.110.82.181:5433
**Database:** wolf_logic
**User:** wolf
**Password:** wolflogic2024

Connection details are embedded in `application_tracker.py`. Update the `ApplicationTracker.__init__()` method if your database configuration changes.

## Files

- `application_tracker.py` - Core API and CLI interface
- `job_cli.py` - Interactive dashboard CLI with formatted output
- `README.md` - This file

## Features

- Complete job application lifecycle tracking
- Email and call logging with timestamps
- Response type categorization
- Interview scheduling with dates
- Automatic audit trail via application_history
- Rich CLI with colored output
- Comprehensive statistics and reporting
- Search and filtering capabilities
- RESTful Python API for programmatic access

## Future Enhancements

- Web dashboard
- Email integration (auto-log sent emails)
- Reminder system for pending actions
- Export to CSV/JSON
- Interview notes storage
- Follow-up email templates
- Analytics and insights
- Multi-user support

## Troubleshooting

### Connection Issues

If you get "password supplied" errors, ensure:
1. Environment is activated: `source ~/anaconda3/bin/activate messiah`
2. PostgreSQL is running on 100.110.82.181:5433
3. Credentials are correct in the code

### Import Errors

If tabulate is not found:
```bash
source ~/anaconda3/bin/activate messiah
pip install tabulate
```

### Database Errors

Check database status:
```bash
source ~/anaconda3/bin/activate messiah
PGPASSWORD='wolflogic2024' psql -U wolf -h 100.110.82.181 -p 5433 -d wolf_logic -c "\dt"
```

## License

Internal use only.
