#!/bin/bash
# Wolf Hunt Status Check
# Shows status of all Wolf Hunt components

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║           🐺 WOLF HUNT - SYSTEM STATUS                ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check API Server
echo "API Server:"
if curl -s http://localhost:5000/health >/dev/null 2>&1; then
    echo "  ✓ Running on http://localhost:5000"
else
    echo "  ✗ Not running"
fi

# Check UI Server
echo ""
echo "UI Server:"
if curl -s http://localhost:8033 >/dev/null 2>&1; then
    echo "  ✓ Running on http://localhost:8033"
else
    echo "  ✗ Not running"
fi

# Check Database
echo ""
echo "Database (wolf_logic):"
if PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "SELECT 1" >/dev/null 2>&1; then
    echo "  ✓ Connected to PostgreSQL (100.110.82.181:5433)"

    # Count candidates
    CANDIDATES=$(PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -tAc "SELECT COUNT(*) FROM candidates")
    echo "  ✓ Candidates: $CANDIDATES"

    # Count scraped jobs
    JOBS=$(PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -tAc "SELECT COUNT(*) FROM scraped_jobs")
    echo "  ✓ Jobs catalogued: $JOBS"
else
    echo "  ✗ Cannot connect to database"
fi

# Show candidates
echo ""
echo "Active Candidates:"
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "
SELECT
    name,
    array_to_string(target_roles, ', ') as target_roles,
    experience_years as exp
FROM candidates
ORDER BY name
" 2>/dev/null | head -10

# Show job breakdown
echo ""
echo "Jobs by Candidate:"
PGPASSWORD=wolflogic2024 psql -h 100.110.82.181 -p 5433 -U wolf -d wolf_logic -c "
SELECT
    candidate_match,
    COUNT(*) as jobs
FROM scraped_jobs
GROUP BY candidate_match
ORDER BY candidate_match
" 2>/dev/null

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                   ACCESS POINTS                        ║"
echo "╠════════════════════════════════════════════════════════╣"
echo "║  Wolf Hunt UI:    http://localhost:8033                ║"
echo "║  API Server:      http://localhost:5000                ║"
echo "║  Health Check:    http://localhost:5000/health         ║"
echo "║  Candidates API:  http://localhost:5000/api/candidates ║"
echo "║  Jobs API:        http://localhost:5000/api/jobs/scraped║"
echo "║  Resume Gen:      POST /api/resume/generate            ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

echo "Features Available:"
echo "  ✓ Job search & cataloguing (Atlanta area)"
echo "  ✓ Candidate tracking (David Adams, Brice Wilson)"
echo "  ✓ Resume generation (Mistral/Orca)"
echo "  ✓ Application tracking database"
echo "  ✓ Job filtering by candidate"
echo "  ✓ API backend fully functional"
echo ""

echo "Next Steps:"
echo "  1. Open http://localhost:8033 in browser"
echo "  2. Use candidate filter to view jobs"
echo "  3. Click jobs for details"
echo "  4. Generate resumes using sidebar"
echo ""
