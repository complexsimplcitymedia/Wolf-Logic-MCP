#!/usr/bin/env python3
"""
Job Application Tracking CLI Dashboard
Interactive command-line tool for managing job applications.
"""

import sys
from datetime import datetime
from tabulate import tabulate
from application_tracker import ApplicationTracker


class Colors:
    """ANSI color codes."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'


def print_header(title: str):
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}{Colors.RESET}\n")


def print_success(msg: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}! {msg}{Colors.RESET}")


def format_timestamp(ts):
    """Format timestamp for display."""
    if not ts:
        return "N/A"
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts)
        except:
            return ts
    return ts.strftime("%Y-%m-%d %H:%M")


def dashboard(tracker: ApplicationTracker):
    """Display main dashboard."""
    print_header("Job Application Tracker Dashboard")

    stats = tracker.get_statistics()

    # Main stats
    print(f"{Colors.BOLD}Overall Statistics:{Colors.RESET}")
    stats_data = [
        ["Total Applications", stats['total_applications']],
        ["Emails Sent", stats['emails_sent']],
        ["Calls Made", stats['calls_made']],
        ["Responses Received", stats['responses_received']],
        ["Interviews Scheduled", stats['interviews_scheduled']],
        ["Avg Call Duration", f"{stats['avg_call_duration']}s" if stats['avg_call_duration'] > 0 else "N/A"],
    ]
    print(tabulate(stats_data, headers=["Metric", "Count"], tablefmt="grid"))

    # Response breakdown
    if stats['response_types']:
        print(f"\n{Colors.BOLD}Response Breakdown:{Colors.RESET}")
        response_data = [[k, v] for k, v in stats['response_types'].items()]
        print(tabulate(response_data, headers=["Response Type", "Count"], tablefmt="grid"))

    # Action items
    pending_calls = tracker.get_pending_calls(days=0)
    pending_responses = tracker.get_pending_responses()
    upcoming_interviews = tracker.get_interviews_upcoming()

    print(f"\n{Colors.BOLD}Action Items:{Colors.RESET}")
    action_data = [
        ["Follow-up Calls Needed", len(pending_calls)],
        ["Awaiting Responses", len(pending_responses)],
        ["Upcoming Interviews", len(upcoming_interviews)],
    ]
    print(tabulate(action_data, headers=["Action", "Count"], tablefmt="grid"))

    # Quick recommendations
    if len(pending_calls) > 0:
        print(f"\n{Colors.YELLOW}Recommendation: {len(pending_calls)} application(s) need follow-up calls{Colors.RESET}")
    if len(pending_responses) > 0:
        print(f"{Colors.YELLOW}Reminder: Waiting on {len(pending_responses)} response(s){Colors.RESET}")


def show_pending_calls(tracker: ApplicationTracker, days: int = 7):
    """Display pending calls."""
    print_header(f"Applications Needing Follow-up ({days}+ days)")

    pending = tracker.get_pending_calls(days=days)

    if not pending:
        print_success("All applications have follow-up calls!")
        return

    table_data = []
    for app in pending:
        days_elapsed = (datetime.now() - datetime.fromisoformat(str(app['date_applied']))).days
        table_data.append([
            app['id'],
            app['company_name'],
            app['position_title'],
            format_timestamp(app['date_applied']),
            days_elapsed
        ])

    print(tabulate(table_data, headers=["ID", "Company", "Position", "Applied", "Days Ago"], tablefmt="grid"))


def show_pending_responses(tracker: ApplicationTracker):
    """Display pending responses."""
    print_header("Applications Awaiting Response")

    pending = tracker.get_pending_responses()

    if not pending:
        print_success("No applications awaiting responses!")
        return

    table_data = []
    for app in pending:
        action = []
        if app['email_sent_date']:
            action.append(f"Email: {format_timestamp(app['email_sent_date'])}")
        if app['call_date']:
            action.append(f"Call: {format_timestamp(app['call_date'])}")
        action_str = " | ".join(action)

        table_data.append([
            app['id'],
            app['company_name'],
            app['position_title'],
            action_str
        ])

    print(tabulate(table_data, headers=["ID", "Company", "Position", "Last Action"], tablefmt="grid"))


def show_upcoming_interviews(tracker: ApplicationTracker):
    """Display upcoming interviews."""
    print_header("Upcoming Interviews")

    upcoming = tracker.get_interviews_upcoming()

    if not upcoming:
        print_success("No upcoming interviews scheduled")
        return

    table_data = []
    for app in upcoming:
        days_until = (datetime.fromisoformat(str(app['interview_date'])) - datetime.now()).days
        table_data.append([
            app['id'],
            app['company_name'],
            app['position_title'],
            format_timestamp(app['interview_date']),
            days_until,
            app['notes'][:30] + "..." if app['notes'] else "N/A"
        ])

    print(tabulate(table_data, headers=["ID", "Company", "Position", "Date", "Days", "Notes"], tablefmt="grid"))


def show_application_details(tracker: ApplicationTracker, app_id: int):
    """Display detailed application info."""
    app = tracker.get_application(app_id)

    if not app:
        print_error(f"Application {app_id} not found")
        return

    print_header(f"Application Details - ID {app_id}")

    details = [
        ["Company", app['company_name']],
        ["Position", app['position_title']],
        ["Job URL", app['job_url'] or "N/A"],
        ["Resume Version", app['resume_version'] or "N/A"],
        ["Applied Date", format_timestamp(app['date_applied'])],
        ["", ""],
        ["Email Sent", "Yes" if app['email_sent'] else "No"],
        ["Email Date", format_timestamp(app['email_sent_date'])],
        ["", ""],
        ["Call Made", "Yes" if app['call_made'] else "No"],
        ["Call Date", format_timestamp(app['call_date'])],
        ["Call Duration", f"{app['call_duration']}s" if app['call_duration'] else "N/A"],
        ["", ""],
        ["Response Received", "Yes" if app['response_received'] else "No"],
        ["Response Type", app['response_type'] or "N/A"],
        ["Response Date", format_timestamp(app['response_date'])],
        ["", ""],
        ["Interview Scheduled", "Yes" if app['interview_scheduled'] else "No"],
        ["Interview Date", format_timestamp(app['interview_date'])],
        ["", ""],
        ["Notes", app['notes'] or "N/A"],
    ]

    for row in details:
        if row[0] == "":
            print()
        else:
            print(f"{Colors.BOLD}{row[0]:<20}{Colors.RESET} {row[1]}")


def list_all_applications(tracker: ApplicationTracker, limit: int = 20):
    """List all applications."""
    print_header(f"All Applications (Last {limit})")

    apps = tracker.get_all_applications(limit=limit)

    if not apps:
        print("No applications found")
        return

    table_data = []
    for app in apps:
        status = []
        if app['email_sent']:
            status.append("Email")
        if app['call_made']:
            status.append("Call")
        if app['response_received']:
            status.append(f"Resp: {app['response_type']}")
        if app['interview_scheduled']:
            status.append("Interview")

        status_str = " | ".join(status) if status else "Pending"

        table_data.append([
            app['id'],
            app['company_name'],
            app['position_title'],
            format_timestamp(app['date_applied']),
            status_str
        ])

    print(tabulate(table_data, headers=["ID", "Company", "Position", "Applied", "Status"], tablefmt="grid"))


def search_applications(tracker: ApplicationTracker, search_type: str, term: str):
    """Search applications."""
    print_header(f"Search Results for '{term}'")

    if search_type == "company":
        results = tracker.search_applications(company=term)
    elif search_type == "position":
        results = tracker.search_applications(position=term)
    else:
        print_error("Search type must be 'company' or 'position'")
        return

    if not results:
        print_warning(f"No results found for {search_type}: {term}")
        return

    table_data = []
    for app in results:
        status = []
        if app['email_sent']:
            status.append("Email")
        if app['call_made']:
            status.append("Call")
        if app['response_received']:
            status.append(f"Resp: {app['response_type']}")
        status_str = " | ".join(status) if status else "Pending"

        table_data.append([
            app['id'],
            app['company_name'],
            app['position_title'],
            format_timestamp(app['date_applied']),
            status_str
        ])

    print(tabulate(table_data, headers=["ID", "Company", "Position", "Applied", "Status"], tablefmt="grid"))


def print_help():
    """Print help message."""
    print(f"""
{Colors.BOLD}Job Application Tracker CLI{Colors.RESET}

{Colors.BOLD}Usage:{Colors.RESET}
  job_cli.py <command> [args]

{Colors.BOLD}Commands:{Colors.RESET}

  {Colors.CYAN}Dashboard & Reporting:{Colors.RESET}
    dashboard              Show main dashboard with statistics
    pending-calls [days]   Show applications needing follow-up (default: 7 days)
    pending-responses      Show applications awaiting response
    upcoming-interviews    Show scheduled interviews
    list [limit]          List all applications (default: 20)
    search <type> <term>  Search by 'company' or 'position'
    details <app_id>      Show detailed application info

  {Colors.CYAN}Adding Applications:{Colors.RESET}
    add-app <company> <position> [url] [resume]
                          Add new application

  {Colors.CYAN}Marking Actions:{Colors.RESET}
    mark-email <app_id> [resume_path]
                          Mark email as sent
    mark-call <app_id> [duration] [notes]
                          Mark call as made (duration in seconds)
    mark-response <app_id> <type> [notes]
                          Mark response received (rejection, callback, interview, etc)
    mark-interview <app_id> [date] [notes]
                          Schedule interview (date format: YYYY-MM-DDTHH:MM:SS)

{Colors.BOLD}Examples:{Colors.RESET}
  job_cli.py dashboard
  job_cli.py pending-calls 7
  job_cli.py add-app "Google" "Software Engineer" "https://careers.google.com/..."
  job_cli.py mark-email 1 "/path/to/resume.pdf"
  job_cli.py mark-call 1 300 "Great discussion about role"
  job_cli.py mark-response 1 callback "Recruiter wants to schedule interview"
  job_cli.py details 1
  job_cli.py list 15
  job_cli.py search company "Google"
""")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    tracker = ApplicationTracker()
    command = sys.argv[1]

    try:
        if command == "dashboard":
            dashboard(tracker)

        elif command == "pending-calls":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            show_pending_calls(tracker, days)

        elif command == "pending-responses":
            show_pending_responses(tracker)

        elif command == "upcoming-interviews":
            show_upcoming_interviews(tracker)

        elif command == "list":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            list_all_applications(tracker, limit)

        elif command == "details":
            if len(sys.argv) < 3:
                print_error("Usage: details <app_id>")
                sys.exit(1)
            app_id = int(sys.argv[2])
            show_application_details(tracker, app_id)

        elif command == "add-app":
            if len(sys.argv) < 4:
                print_error("Usage: add-app <company> <position> [url] [resume]")
                sys.exit(1)
            company = sys.argv[2]
            position = sys.argv[3]
            url = sys.argv[4] if len(sys.argv) > 4 else None
            resume = sys.argv[5] if len(sys.argv) > 5 else None
            app_id = tracker.add_application(company, position, url, resume)
            print_success(f"Added application (ID: {app_id})")

        elif command == "mark-email":
            if len(sys.argv) < 3:
                print_error("Usage: mark-email <app_id> [resume_path]")
                sys.exit(1)
            app_id = int(sys.argv[2])
            resume_path = sys.argv[3] if len(sys.argv) > 3 else None
            tracker.mark_email_sent(app_id, resume_path)
            print_success(f"Marked email as sent for application {app_id}")

        elif command == "mark-call":
            if len(sys.argv) < 3:
                print_error("Usage: mark-call <app_id> [duration] [notes]")
                sys.exit(1)
            app_id = int(sys.argv[2])
            duration = int(sys.argv[3]) if len(sys.argv) > 3 else None
            notes = sys.argv[4] if len(sys.argv) > 4 else None
            tracker.mark_call_made(app_id, duration, notes)
            print_success(f"Marked call as made for application {app_id}")

        elif command == "mark-response":
            if len(sys.argv) < 4:
                print_error("Usage: mark-response <app_id> <type> [notes]")
                sys.exit(1)
            app_id = int(sys.argv[2])
            response_type = sys.argv[3]
            notes = sys.argv[4] if len(sys.argv) > 4 else None
            tracker.mark_response(app_id, response_type, notes)
            print_success(f"Marked response for application {app_id}")

        elif command == "mark-interview":
            if len(sys.argv) < 3:
                print_error("Usage: mark-interview <app_id> [date] [notes]")
                sys.exit(1)
            app_id = int(sys.argv[2])
            interview_date = None
            if len(sys.argv) > 3:
                try:
                    interview_date = datetime.fromisoformat(sys.argv[3])
                except:
                    print_error("Invalid date format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
                    sys.exit(1)
            notes = sys.argv[4] if len(sys.argv) > 4 else None
            tracker.schedule_interview(app_id, interview_date, notes)
            print_success(f"Scheduled interview for application {app_id}")

        elif command == "search":
            if len(sys.argv) < 4:
                print_error("Usage: search <company|position> <term>")
                sys.exit(1)
            search_type = sys.argv[2]
            term = sys.argv[3]
            search_applications(tracker, search_type, term)

        elif command == "-h" or command == "--help" or command == "help":
            print_help()

        else:
            print_error(f"Unknown command: {command}")
            print_help()
            sys.exit(1)

    except Exception as e:
        print_error(f"Error: {e}")
        sys.exit(1)
    finally:
        tracker.close()


if __name__ == "__main__":
    main()
