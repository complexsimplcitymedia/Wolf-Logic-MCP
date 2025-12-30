#!/usr/bin/env python3
"""
Job Application Tracking API
Tracks job applications, communications, and interview progress.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import Optional, Dict, List, Tuple


class ApplicationTracker:
    """Database interface for job application tracking."""

    def __init__(self,
                 host: str = "localhost",
                 port: int = 5433,
                 database: str = "wolf_logic",
                 user: str = "wolf",
                 password: str = "wolflogic2024"):
        """Initialize database connection."""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
        except psycopg2.Error as e:
            raise Exception(f"Database connection failed: {e}")

    def _execute(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute query and return results."""
        try:
            cur = self.conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params)
            self.conn.commit()

            # Return results if SELECT query
            if query.strip().upper().startswith('SELECT'):
                return cur.fetchall()

            # Return last insert id if INSERT
            if query.strip().upper().startswith('INSERT'):
                cur.execute("SELECT lastval() as id")
                result = cur.fetchone()
                return result['id'] if result else None

            cur.close()
            return None
        except psycopg2.Error as e:
            self.conn.rollback()
            raise Exception(f"Query execution failed: {e}")

    def add_application(self,
                       company: str,
                       position: str,
                       job_url: str = None,
                       resume_version: str = None) -> int:
        """Add new job application to database.

        Args:
            company: Company name
            position: Job position title
            job_url: URL of job posting (optional)
            resume_version: Resume version used (optional)

        Returns:
            Application ID
        """
        query = """
            INSERT INTO job_applications
            (company_name, position_title, job_url, resume_version, date_applied)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            RETURNING id
        """
        result = self._execute(query, (company, position, job_url, resume_version))

        # Log to history
        self._log_history(result, "APPLICATION_ADDED",
                         f"New application: {company} - {position}")

        return result

    def mark_email_sent(self, application_id: int, resume_path: str = None) -> bool:
        """Mark email as sent for an application.

        Args:
            application_id: Application ID
            resume_path: Path to resume file sent (optional)

        Returns:
            Success status
        """
        query = """
            UPDATE job_applications
            SET email_sent = TRUE, email_sent_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        self._execute(query, (application_id,))

        details = f"Email sent"
        if resume_path:
            details += f" with resume: {resume_path}"

        self._log_history(application_id, "EMAIL_SENT", details)
        return True

    def mark_call_made(self,
                      application_id: int,
                      duration: int = None,
                      notes: str = None) -> bool:
        """Mark phone call as made for an application.

        Args:
            application_id: Application ID
            duration: Call duration in seconds (optional)
            notes: Call notes (optional)

        Returns:
            Success status
        """
        query = """
            UPDATE job_applications
            SET call_made = TRUE, call_date = CURRENT_TIMESTAMP,
                call_duration = %s, notes = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        self._execute(query, (duration, notes, application_id))

        details = "Call made"
        if duration:
            details += f" - Duration: {duration}s"
        if notes:
            details += f" - Notes: {notes}"

        self._log_history(application_id, "CALL_MADE", details)
        return True

    def mark_response(self,
                     application_id: int,
                     response_type: str,
                     notes: str = None) -> bool:
        """Mark response received from employer.

        Args:
            application_id: Application ID
            response_type: Type of response (rejection, callback, interview, etc.)
            notes: Response details (optional)

        Returns:
            Success status
        """
        query = """
            UPDATE job_applications
            SET response_received = TRUE, response_type = %s,
                response_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        self._execute(query, (response_type, application_id))

        if notes:
            # Update notes field
            query_notes = "UPDATE job_applications SET notes = %s WHERE id = %s"
            self._execute(query_notes, (notes, application_id))

        details = f"Response received: {response_type}"
        if notes:
            details += f" - {notes}"

        self._log_history(application_id, "RESPONSE_RECEIVED", details)
        return True

    def schedule_interview(self,
                          application_id: int,
                          interview_date: datetime = None,
                          notes: str = None) -> bool:
        """Mark interview as scheduled.

        Args:
            application_id: Application ID
            interview_date: Interview date/time (optional)
            notes: Interview details (optional)

        Returns:
            Success status
        """
        query = """
            UPDATE job_applications
            SET interview_scheduled = TRUE, interview_date = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """
        self._execute(query, (interview_date, application_id))

        if notes:
            query_notes = "UPDATE job_applications SET notes = %s WHERE id = %s"
            self._execute(query_notes, (notes, application_id))

        details = "Interview scheduled"
        if interview_date:
            details += f" for {interview_date.isoformat()}"
        if notes:
            details += f" - {notes}"

        self._log_history(application_id, "INTERVIEW_SCHEDULED", details)
        return True

    def get_application(self, application_id: int) -> Optional[Dict]:
        """Get single application details.

        Args:
            application_id: Application ID

        Returns:
            Application record or None
        """
        query = "SELECT * FROM job_applications WHERE id = %s"
        results = self._execute(query, (application_id,))
        return results[0] if results else None

    def get_statistics(self) -> Dict:
        """Get application tracking statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {}

        # Total applications
        query = "SELECT COUNT(*) as count FROM job_applications"
        result = self._execute(query)
        stats['total_applications'] = result[0]['count'] if result else 0

        # Emails sent
        query = "SELECT COUNT(*) as count FROM job_applications WHERE email_sent = TRUE"
        result = self._execute(query)
        stats['emails_sent'] = result[0]['count'] if result else 0

        # Calls made
        query = "SELECT COUNT(*) as count FROM job_applications WHERE call_made = TRUE"
        result = self._execute(query)
        stats['calls_made'] = result[0]['count'] if result else 0

        # Responses received
        query = "SELECT COUNT(*) as count FROM job_applications WHERE response_received = TRUE"
        result = self._execute(query)
        stats['responses_received'] = result[0]['count'] if result else 0

        # Response breakdown
        query = """
            SELECT response_type, COUNT(*) as count
            FROM job_applications
            WHERE response_received = TRUE
            GROUP BY response_type
        """
        result = self._execute(query)
        stats['response_types'] = {row['response_type']: row['count'] for row in result} if result else {}

        # Interviews scheduled
        query = "SELECT COUNT(*) as count FROM job_applications WHERE interview_scheduled = TRUE"
        result = self._execute(query)
        stats['interviews_scheduled'] = result[0]['count'] if result else 0

        # Average call duration
        query = """
            SELECT AVG(call_duration) as avg_duration
            FROM job_applications
            WHERE call_made = TRUE AND call_duration IS NOT NULL
        """
        result = self._execute(query)
        stats['avg_call_duration'] = int(result[0]['avg_duration']) if result and result[0]['avg_duration'] else 0

        return stats

    def get_pending_calls(self, days: int = 7) -> List[Dict]:
        """Get applications that need follow-up calls.

        Applications without calls in the past N days.

        Args:
            days: Look back this many days (default 7)

        Returns:
            List of applications needing follow-up
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = """
            SELECT
                id, company_name, position_title, date_applied,
                email_sent_date, call_date, response_received, notes
            FROM job_applications
            WHERE call_made = FALSE
            AND date_applied <= %s
            AND response_received = FALSE
            ORDER BY date_applied ASC
        """
        results = self._execute(query, (cutoff_date,))
        return results if results else []

    def get_pending_responses(self) -> List[Dict]:
        """Get applications awaiting response from employer.

        Returns:
            List of applications without responses
        """
        query = """
            SELECT
                id, company_name, position_title, date_applied,
                email_sent_date, call_date
            FROM job_applications
            WHERE response_received = FALSE
            AND (email_sent = TRUE OR call_made = TRUE)
            ORDER BY date_applied ASC
        """
        results = self._execute(query)
        return results if results else []

    def get_interviews_upcoming(self) -> List[Dict]:
        """Get upcoming interviews.

        Returns:
            List of scheduled interviews ordered by date
        """
        query = """
            SELECT
                id, company_name, position_title, interview_date, notes
            FROM job_applications
            WHERE interview_scheduled = TRUE
            AND interview_date > CURRENT_TIMESTAMP
            ORDER BY interview_date ASC
        """
        results = self._execute(query)
        return results if results else []

    def get_all_applications(self,
                            limit: int = None,
                            order_by: str = "date_applied DESC") -> List[Dict]:
        """Get all applications with optional filtering.

        Args:
            limit: Limit results to N records
            order_by: SQL order by clause

        Returns:
            List of applications
        """
        query = f"SELECT * FROM job_applications ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"

        results = self._execute(query)
        return results if results else []

    def search_applications(self,
                           company: str = None,
                           position: str = None) -> List[Dict]:
        """Search applications by company or position.

        Args:
            company: Company name (partial match)
            position: Position title (partial match)

        Returns:
            List of matching applications
        """
        conditions = []
        params = []

        if company:
            conditions.append("company_name ILIKE %s")
            params.append(f"%{company}%")

        if position:
            conditions.append("position_title ILIKE %s")
            params.append(f"%{position}%")

        if not conditions:
            return []

        query = f"SELECT * FROM job_applications WHERE {' AND '.join(conditions)} ORDER BY date_applied DESC"
        results = self._execute(query, tuple(params))
        return results if results else []

    def _log_history(self, application_id: int, action: str, details: str = None):
        """Log action to application history.

        Args:
            application_id: Application ID
            action: Action type
            details: Action details
        """
        query = """
            INSERT INTO application_history (application_id, action, details)
            VALUES (%s, %s, %s)
        """
        try:
            self._execute(query, (application_id, action, details))
        except Exception as e:
            print(f"Warning: Failed to log history: {e}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


# Convenience functions
def get_tracker() -> ApplicationTracker:
    """Get application tracker instance."""
    return ApplicationTracker()


def main():
    """CLI interface for tracker."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python application_tracker.py <command> [args]")
        print("\nCommands:")
        print("  add <company> <position> [url] [resume]")
        print("  email_sent <app_id> [resume_path]")
        print("  call_made <app_id> [duration] [notes]")
        print("  response <app_id> <type> [notes]")
        print("  interview <app_id> [date] [notes]")
        print("  stats")
        print("  pending_calls [days]")
        print("  pending_responses")
        print("  upcoming_interviews")
        print("  get <app_id>")
        print("  list [limit]")
        print("  search <company|position> <term>")
        sys.exit(1)

    tracker = get_tracker()
    command = sys.argv[1]

    try:
        if command == "add":
            if len(sys.argv) < 4:
                print("Usage: add <company> <position> [url] [resume]")
                sys.exit(1)
            company = sys.argv[2]
            position = sys.argv[3]
            url = sys.argv[4] if len(sys.argv) > 4 else None
            resume = sys.argv[5] if len(sys.argv) > 5 else None
            app_id = tracker.add_application(company, position, url, resume)
            print(f"Added application (ID: {app_id})")

        elif command == "email_sent":
            if len(sys.argv) < 3:
                print("Usage: email_sent <app_id> [resume_path]")
                sys.exit(1)
            app_id = int(sys.argv[2])
            resume_path = sys.argv[3] if len(sys.argv) > 3 else None
            tracker.mark_email_sent(app_id, resume_path)
            print(f"Marked email as sent for application {app_id}")

        elif command == "call_made":
            if len(sys.argv) < 3:
                print("Usage: call_made <app_id> [duration] [notes]")
                sys.exit(1)
            app_id = int(sys.argv[2])
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else None
            notes = sys.argv[4] if len(sys.argv) > 4 else None
            tracker.mark_call_made(app_id, duration, notes)
            print(f"Marked call as made for application {app_id}")

        elif command == "response":
            if len(sys.argv) < 4:
                print("Usage: response <app_id> <type> [notes]")
                sys.exit(1)
            app_id = int(sys.argv[2])
            response_type = sys.argv[3]
            notes = sys.argv[4] if len(sys.argv) > 4 else None
            tracker.mark_response(app_id, response_type, notes)
            print(f"Marked response for application {app_id}")

        elif command == "interview":
            if len(sys.argv) < 3:
                print("Usage: interview <app_id> [date] [notes]")
                sys.exit(1)
            app_id = int(sys.argv[2])
            interview_date = None
            if len(sys.argv) > 3:
                try:
                    interview_date = datetime.fromisoformat(sys.argv[3])
                except:
                    print("Invalid date format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
                    sys.exit(1)
            notes = sys.argv[4] if len(sys.argv) > 4 else None
            tracker.schedule_interview(app_id, interview_date, notes)
            print(f"Scheduled interview for application {app_id}")

        elif command == "stats":
            stats = tracker.get_statistics()
            print("\nApplication Statistics:")
            print(f"  Total Applications: {stats['total_applications']}")
            print(f"  Emails Sent: {stats['emails_sent']}")
            print(f"  Calls Made: {stats['calls_made']}")
            print(f"  Responses Received: {stats['responses_received']}")
            if stats['response_types']:
                print("  Response Types:")
                for rtype, count in stats['response_types'].items():
                    print(f"    {rtype}: {count}")
            print(f"  Interviews Scheduled: {stats['interviews_scheduled']}")
            print(f"  Average Call Duration: {stats['avg_call_duration']}s")

        elif command == "pending_calls":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            pending = tracker.get_pending_calls(days)
            print(f"\nApplications Needing Follow-up Calls ({days} days+):")
            if pending:
                for app in pending:
                    print(f"  [{app['id']}] {app['company_name']} - {app['position_title']}")
                    print(f"      Applied: {app['date_applied']}")
            else:
                print("  No pending calls needed")

        elif command == "pending_responses":
            pending = tracker.get_pending_responses()
            print(f"\nApplications Awaiting Response:")
            if pending:
                for app in pending:
                    print(f"  [{app['id']}] {app['company_name']} - {app['position_title']}")
                    print(f"      Applied: {app['date_applied']}")
            else:
                print("  No pending responses")

        elif command == "upcoming_interviews":
            upcoming = tracker.get_interviews_upcoming()
            print(f"\nUpcoming Interviews:")
            if upcoming:
                for app in upcoming:
                    print(f"  [{app['id']}] {app['company_name']} - {app['position_title']}")
                    print(f"      Date: {app['interview_date']}")
            else:
                print("  No upcoming interviews")

        elif command == "get":
            if len(sys.argv) < 3:
                print("Usage: get <app_id>")
                sys.exit(1)
            app_id = int(sys.argv[2])
            app = tracker.get_application(app_id)
            if app:
                print(f"\nApplication {app_id}:")
                for key, value in app.items():
                    print(f"  {key}: {value}")
            else:
                print(f"Application {app_id} not found")

        elif command == "list":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            apps = tracker.get_all_applications(limit=limit)
            print(f"\nLast {limit} Applications:")
            for app in apps:
                status = []
                if app['email_sent']:
                    status.append("Email")
                if app['call_made']:
                    status.append("Called")
                if app['response_received']:
                    status.append(f"Response: {app['response_type']}")
                if app['interview_scheduled']:
                    status.append("Interview")
                status_str = " | ".join(status) if status else "No action"
                print(f"  [{app['id']}] {app['company_name']} - {app['position_title']}")
                print(f"      Applied: {app['date_applied']} | {status_str}")

        elif command == "search":
            if len(sys.argv) < 4:
                print("Usage: search <company|position> <term>")
                sys.exit(1)
            search_type = sys.argv[2]
            term = sys.argv[3]

            if search_type == "company":
                results = tracker.search_applications(company=term)
            elif search_type == "position":
                results = tracker.search_applications(position=term)
            else:
                print("Search type must be 'company' or 'position'")
                sys.exit(1)

            print(f"\nSearch Results for '{term}':")
            if results:
                for app in results:
                    print(f"  [{app['id']}] {app['company_name']} - {app['position_title']}")
            else:
                print("  No results found")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    finally:
        tracker.close()


if __name__ == "__main__":
    main()
