# Job Application Tracker - Quick Start Guide

## One-Time Setup

```bash
# Activate environment
source ~/anaconda3/bin/activate messiah

# Navigate to tracking directory
cd /mnt/Wolf-code/Wolf-Ai-Enterptises/tracking

# Verify database connection
python application_tracker.py list
```

## Daily Usage Patterns

### Morning: Check Dashboard

```bash
python job_cli.py dashboard
```

Shows:
- Total applications added
- Emails sent, calls made, responses received
- Interviews scheduled
- **Action items** - What needs follow-up

### New Application

```bash
python job_cli.py add-app "CompanyName" "Job Title" "https://link.to.job" "v1.0"
```

Returns: Application ID (use this for future updates)

### After Sending Email

```bash
python job_cli.py mark-email 1 "/path/to/resume.pdf"
```

Optional: Include resume path for reference

### After Phone Call

```bash
python job_cli.py mark-call 1 300 "Discussed role, tech stack, timeline"
```

Arguments:
- App ID: `1`
- Duration: `300` (seconds)
- Notes: Your call summary

### Response Received

```bash
python job_cli.py mark-response 1 callback "Wants to schedule technical round"
```

Common response types:
- `rejection` - Rejected
- `callback` - Asked to call back / follow up
- `interview` - Interview scheduled
- `scheduled` - Time/date given for next step

### Schedule Interview

```bash
python job_cli.py mark-interview 1 "2025-12-15T14:00:00" "Technical interview with hiring manager"
```

Date format: `YYYY-MM-DDTHH:MM:SS` (ISO 8601)

### What Needs Attention?

```bash
# Show applications that haven't had calls (7+ days old)
python job_cli.py pending-calls 7

# Show applications waiting for response
python job_cli.py pending-responses

# Show upcoming interviews
python job_cli.py upcoming-interviews
```

### View Application Details

```bash
python job_cli.py details 1
```

Shows complete timeline and all actions taken.

### Search Applications

```bash
# Find all Google applications
python job_cli.py search company Google

# Find all Engineer positions
python job_cli.py search position Engineer
```

## Reporting

### Weekly Summary

```bash
python job_cli.py dashboard
```

### Top Prospects (Pending Responses)

```bash
python job_cli.py pending-responses
```

### Follow-up Needed

```bash
# Show applications 3+ days old without calls
python job_cli.py pending-calls 3
```

## Command Cheat Sheet

| Task | Command |
|------|---------|
| Dashboard | `python job_cli.py dashboard` |
| Add app | `python job_cli.py add-app "Company" "Role" "URL"` |
| Send email | `python job_cli.py mark-email <id> [resume_path]` |
| Log call | `python job_cli.py mark-call <id> <seconds> [notes]` |
| Record response | `python job_cli.py mark-response <id> <type> [notes]` |
| Schedule interview | `python job_cli.py mark-interview <id> [date] [notes]` |
| View details | `python job_cli.py details <id>` |
| List all | `python job_cli.py list [limit]` |
| Pending calls | `python job_cli.py pending-calls [days]` |
| Pending responses | `python job_cli.py pending-responses` |
| Upcoming interviews | `python job_cli.py upcoming-interviews` |
| Search | `python job_cli.py search company/position <term>` |

## Example: Full Workflow

```bash
# Day 1: Find job, add to system
python job_cli.py add-app "Google" "Senior Software Engineer" "https://careers.google.com/..." "v2.1"
# Returns: Application ID 5

# Day 1: Send resume
python job_cli.py mark-email 5 "/home/my_resume_2024.pdf"

# Day 3: Recruiter calls, you call back
python job_cli.py mark-call 5 480 "Discussed role, tech stack, compensation expectations. Recruiter liked responses."

# Day 3: Recruiter sends next steps
python job_cli.py mark-response 5 callback "Wants to schedule technical interview next week"

# Day 7: Schedule the interview
python job_cli.py mark-interview 5 "2025-12-20T10:00:00" "2-hour technical interview panel"

# Day 7: Check what's happening next
python job_cli.py upcoming-interviews

# Day 15: Check overall progress
python job_cli.py dashboard
```

## Database Direct Access

Query the database directly if needed:

```bash
source ~/anaconda3/bin/activate messiah

PGPASSWORD='wolflogic2024' psql -U wolf -h localhost -p 5433 -d wolf_logic

# Example queries:
SELECT id, company_name, position_title, date_applied FROM job_applications
ORDER BY date_applied DESC LIMIT 10;

SELECT company_name, COUNT(*) as count FROM job_applications
GROUP BY company_name;
```

## Tips & Tricks

1. **Use aliases** - Create shell alias for faster typing:
   ```bash
   alias jc='python /mnt/Wolf-code/Wolf-Ai-Enterptises/tracking/job_cli.py'
   # Then: jc dashboard
   ```

2. **Check pending every morning** - Makes prioritization easy:
   ```bash
   python job_cli.py pending-calls 3
   python job_cli.py pending-responses
   ```

3. **Add notes liberally** - Future you will appreciate the context

4. **Accurate call duration** - Helps with statistics on engagement depth

5. **Search before adding** - Avoid duplicate applications:
   ```bash
   python job_cli.py search company Google
   ```

## Troubleshooting

**"Permission denied" error**
```bash
chmod +x /mnt/Wolf-code/Wolf-Ai-Enterptises/tracking/job_cli.py
```

**"ModuleNotFoundError: No module named 'psycopg2'"**
```bash
source ~/anaconda3/bin/activate messiah
pip install psycopg2-binary
```

**Database connection fails**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify credentials in `application_tracker.py`
- Test connection: `PGPASSWORD='wolflogic2024' psql -U wolf -h localhost -p 5433 -d wolf_logic -c "SELECT 1"`

## Getting Help

From anywhere with the CLI:
```bash
python job_cli.py help
```

Or check the detailed README:
```bash
cat /mnt/Wolf-code/Wolf-Ai-Enterptises/tracking/README.md
```

---

**Remember:** The system tracks everything. Focus on regular follow-ups and accurate logging. The dashboard will show you your progress over time.
