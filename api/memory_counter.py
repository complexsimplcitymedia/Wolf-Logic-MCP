#!/usr/bin/env python3
"""
Live Memory Counter - Real-time database stats
For dashboard display and button integration
"""

import json
import sys
import psycopg2
from datetime import datetime

PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}


def get_memory_stats():
    """Get comprehensive memory statistics"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()

        # Total memories
        cur.execute("SELECT COUNT(*) FROM memories")
        total = cur.fetchone()[0]

        # Last updated
        cur.execute("SELECT MAX(created_at) FROM memories")
        last_updated = cur.fetchone()[0]

        # Today's count
        cur.execute("""
            SELECT COUNT(*) FROM memories
            WHERE created_at >= CURRENT_DATE
        """)
        today_count = cur.fetchone()[0]

        # Last hour count
        cur.execute("""
            SELECT COUNT(*) FROM memories
            WHERE created_at >= NOW() - INTERVAL '1 hour'
        """)
        last_hour = cur.fetchone()[0]

        # Top namespace
        cur.execute("""
            SELECT namespace, COUNT(*) as count
            FROM memories
            GROUP BY namespace
            ORDER BY count DESC
            LIMIT 1
        """)
        top_namespace = cur.fetchone()

        # Average per day (last 7 days)
        cur.execute("""
            SELECT ROUND(COUNT(*)::numeric / 7, 0)
            FROM memories
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        avg_per_day = cur.fetchone()[0]

        cur.close()
        conn.close()

        return {
            "success": True,
            "total_memories": int(total),
            "last_updated": last_updated.isoformat() if last_updated else None,
            "today_count": int(today_count),
            "last_hour_count": int(last_hour),
            "top_namespace": {
                "name": top_namespace[0] if top_namespace else None,
                "count": int(top_namespace[1]) if top_namespace else 0
            },
            "avg_per_day_7d": int(avg_per_day) if avg_per_day else 0,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to get memory stats: {e}"
        }


def main():
    """Output JSON for API consumption"""
    stats = get_memory_stats()
    print(json.dumps(stats, indent=2))
    sys.exit(0 if stats["success"] else 1)


if __name__ == "__main__":
    main()
