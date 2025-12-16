#!/usr/bin/env python3
"""
Bulk import tool for job applications.
Import applications from CSV file into the tracking system.
"""

import sys
import csv
from datetime import datetime
from application_tracker import ApplicationTracker


def import_csv(csv_file: str, dry_run: bool = False) -> int:
    """Import applications from CSV file.

    CSV format (header required):
    company_name, position_title, job_url, resume_version, date_applied, notes

    Args:
        csv_file: Path to CSV file
        dry_run: If True, show what would be imported without saving

    Returns:
        Number of applications imported
    """
    tracker = ApplicationTracker()
    imported = 0
    errors = 0

    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                print("Error: CSV file is empty")
                return 0

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                try:
                    company = row.get('company_name', '').strip()
                    position = row.get('position_title', '').strip()
                    job_url = row.get('job_url', '').strip() or None
                    resume_version = row.get('resume_version', '').strip() or None
                    notes = row.get('notes', '').strip() or None

                    # Validate required fields
                    if not company or not position:
                        print(f"Row {row_num}: Skipped - missing company_name or position_title")
                        errors += 1
                        continue

                    if dry_run:
                        print(f"Row {row_num}: Would import {company} - {position}")
                    else:
                        app_id = tracker.add_application(
                            company=company,
                            position=position,
                            job_url=job_url,
                            resume_version=resume_version
                        )

                        if notes:
                            # Update notes field
                            query = "UPDATE job_applications SET notes = %s WHERE id = %s"
                            tracker._execute(query, (notes, app_id))

                        print(f"Row {row_num}: Imported {company} - {position} (ID: {app_id})")
                        imported += 1

                except Exception as e:
                    print(f"Row {row_num}: Error - {e}")
                    errors += 1

    except FileNotFoundError:
        print(f"Error: File not found: {csv_file}")
        return 0
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return 0
    finally:
        tracker.close()

    print(f"\nSummary: {imported} imported, {errors} errors")
    return imported


def export_csv(csv_file: str) -> int:
    """Export applications to CSV file.

    Args:
        csv_file: Path to output CSV file

    Returns:
        Number of applications exported
    """
    tracker = ApplicationTracker()
    exported = 0

    try:
        apps = tracker.get_all_applications(limit=None)

        if not apps:
            print("No applications to export")
            return 0

        with open(csv_file, 'w', newline='') as f:
            fieldnames = [
                'id', 'company_name', 'position_title', 'job_url',
                'resume_version', 'date_applied', 'email_sent', 'call_made',
                'response_received', 'response_type', 'interview_scheduled',
                'interview_date', 'notes'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for app in apps:
                row = {
                    'id': app['id'],
                    'company_name': app['company_name'],
                    'position_title': app['position_title'],
                    'job_url': app['job_url'] or '',
                    'resume_version': app['resume_version'] or '',
                    'date_applied': app['date_applied'],
                    'email_sent': 'Yes' if app['email_sent'] else 'No',
                    'call_made': 'Yes' if app['call_made'] else 'No',
                    'response_received': 'Yes' if app['response_received'] else 'No',
                    'response_type': app['response_type'] or '',
                    'interview_scheduled': 'Yes' if app['interview_scheduled'] else 'No',
                    'interview_date': app['interview_date'] or '',
                    'notes': app['notes'] or ''
                }
                writer.writerow(row)
                exported += 1

        print(f"Exported {exported} applications to {csv_file}")
        return exported

    except Exception as e:
        print(f"Error exporting CSV: {e}")
        return 0
    finally:
        tracker.close()


def create_sample_csv(csv_file: str):
    """Create a sample CSV file for import.

    Args:
        csv_file: Path to output sample CSV
    """
    sample_data = [
        ['company_name', 'position_title', 'job_url', 'resume_version', 'notes'],
        ['Google', 'Software Engineer', 'https://careers.google.com/jobs/...', 'v1.0', 'Applied via web portal'],
        ['Microsoft', 'Cloud Architect', 'https://careers.microsoft.com/jobs/...', 'v1.0', 'Referred by John Smith'],
        ['Apple', 'ML Engineer', 'https://careers.apple.com/jobs/...', 'v2.0', 'Posted on job board'],
        ['Amazon', 'Senior Backend Engineer', '', 'v1.0', 'Recruiter contact'],
    ]

    try:
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(sample_data)
        print(f"Sample CSV created at {csv_file}")
    except Exception as e:
        print(f"Error creating sample CSV: {e}")


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python bulk_import.py <command> [args]")
        print("\nCommands:")
        print("  import <csv_file>         Import applications from CSV")
        print("  import-dry <csv_file>     Preview what would be imported (no changes)")
        print("  export <csv_file>         Export all applications to CSV")
        print("  sample <csv_file>         Create sample CSV template")
        print("\nCSV Format (for import):")
        print("  Headers: company_name, position_title, job_url, resume_version, notes")
        print("  Required: company_name, position_title")
        print("  Optional: job_url, resume_version, notes")
        sys.exit(1)

    command = sys.argv[1]

    if command == "import":
        if len(sys.argv) < 3:
            print("Usage: import <csv_file>")
            sys.exit(1)
        csv_file = sys.argv[2]
        import_csv(csv_file, dry_run=False)

    elif command == "import-dry":
        if len(sys.argv) < 3:
            print("Usage: import-dry <csv_file>")
            sys.exit(1)
        csv_file = sys.argv[2]
        print("DRY RUN - No changes will be made\n")
        import_csv(csv_file, dry_run=True)

    elif command == "export":
        if len(sys.argv) < 3:
            print("Usage: export <csv_file>")
            sys.exit(1)
        csv_file = sys.argv[2]
        export_csv(csv_file)

    elif command == "sample":
        if len(sys.argv) < 3:
            csv_file = "applications_sample.csv"
        else:
            csv_file = sys.argv[2]
        create_sample_csv(csv_file)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
