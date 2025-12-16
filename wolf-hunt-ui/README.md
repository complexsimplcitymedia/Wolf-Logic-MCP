# Wolf Hunt UI - Job Search Command Center

## Access

**http://localhost:3333**

## Features

✓ Multi-board search across 7 job boards simultaneously
✓ Resume generator integration
✓ Application tracker
✓ Bulk apply operations
✓ Campaign management dashboard
✓ CSV export

## Job Boards (ROCN Layer)

- ZipRecruiter
- Indeed  
- Remotive
- GraphQL Jobs
- GameBrain
- Fantastic Jobs
- WhatJobs

## Quick Start

1. Open http://localhost:3333
2. Enter job keywords (default: "software engineer")
3. Enter location (default: "remote")
4. Select which boards to search
5. Click **HUNT**

## Features

### Job Search
- Search all 7 boards at once
- Filter by location (including remote)
- Sort by date, source, or title
- Export results to CSV

### Resume Generator
- Enter target job title
- Generates ATS-optimized resume
- Tailored to specific positions

### Application Tracker
- Track all applications
- Monitor response rates
- Schedule follow-ups

### Bulk Operations
- Select multiple jobs
- Apply to many positions at once
- Automated resume generation

### Campaign Management
- Voice agent status
- Email campaign status
- Launch coordinated outreach

## File Structure

```
wolf-hunt-ui/
├── index.html              # Main UI
├── server.py              # Python HTTP server
├── static/
│   ├── css/
│   │   └── hunt.css       # Terminal-style design
│   └── js/
│       └── hunt.js        # Job search logic
└── README.md
```

## Server Control

```bash
# Start (already running on port 3333)
python server.py 3333

# Stop
pkill -f "server.py 3333"

# Check if running
curl -I http://localhost:3333
```

## Integration

Currently using mock data. To connect to real MCP servers, update `hunt.js` line 61:

```javascript
// Replace mock implementation with real MCP calls
const response = await fetch(`${this.config.apiBase}/mcp/${board}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, location })
});
```

## Next Steps

1. Wire MCP servers to UI backend
2. Connect resume generator
3. Hook up PostgreSQL tracker
4. Enable voice/email campaigns
5. Deploy to Caddy (optional)

---

**The hunt begins.**
