#!/usr/bin/env python3
"""
Visual Dashboard - Button-Ready Version
Generates charts + returns JSON status for API/button integration
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import psycopg2
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from collections import defaultdict

# Database
PG_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Output
CHARTS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/metrics/charts")
CHARTS_DIR.mkdir(parents=True, exist_ok=True)


class VisualDashboard:
    """Generate visual charts and graphs with API-friendly output"""

    def __init__(self, json_output=False):
        self.conn = None
        self.json_output = json_output
        plt.style.use('dark_background')

    def log(self, message):
        """Log messages (suppressed in JSON mode)"""
        if not self.json_output:
            print(message)

    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(**PG_CONFIG)
            return True
        except Exception as e:
            if self.json_output:
                print(json.dumps({"success": False, "error": str(e)}))
            else:
                print(f"Database connection failed: {e}")
            return False

    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()

    def get_activity_timeline(self, days=30):
        """Get memory creation timeline"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT
                    DATE(created_at) as date,
                    user_id,
                    COUNT(*) as count
                FROM memories
                WHERE created_at > NOW() - INTERVAL '%s days'
                GROUP BY DATE(created_at), user_id
                ORDER BY date
            """, (days,))
            return cur.fetchall()

    def get_namespace_distribution(self):
        """Get namespace memory counts"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT namespace, COUNT(*) as count
                FROM memories
                WHERE namespace IS NOT NULL
                GROUP BY namespace
                ORDER BY count DESC
                LIMIT 6
            """)
            return cur.fetchall()

    def get_hourly_activity(self):
        """Get activity by hour of day"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as count
                FROM memories
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY hour
            """)
            return cur.fetchall()

    def plot_activity_timeline(self, days=30):
        """Line chart: memory creation over time"""
        data = self.get_activity_timeline(days)

        # Group by agent
        agents = defaultdict(lambda: defaultdict(int))
        for date, user_id, count in data:
            agents[user_id][date] = count

        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot top 5 agents only
        for agent_id in list(agents.keys())[:5]:
            dates = agents[agent_id]
            sorted_dates = sorted(dates.keys())
            counts = [dates[d] for d in sorted_dates]
            ax.plot(sorted_dates, counts, marker='o', label=agent_id, linewidth=2)

        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Memories Created', fontsize=12, fontweight='bold')
        ax.set_title(f'Activity Timeline (Last {days} Days)', fontsize=16, fontweight='bold')
        ax.legend(loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)
        plt.tight_layout()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = CHARTS_DIR / f"timeline_{timestamp}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        return output_file

    def plot_namespace_distribution(self):
        """Doughnut chart: namespace distribution"""
        data = self.get_namespace_distribution()
        namespaces = [row[0] for row in data]
        counts = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(12, 8))
        colors = plt.cm.Set3(range(len(namespaces)))

        wedges, texts, autotexts = ax.pie(
            counts,
            labels=namespaces,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.set_title('Memory Distribution by Namespace', fontsize=16, fontweight='bold', pad=20)
        plt.tight_layout()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = CHARTS_DIR / f"namespaces_{timestamp}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        return output_file

    def plot_hourly_heatmap(self):
        """Bar chart: activity by hour"""
        data = self.get_hourly_activity()
        hours = [int(row[0]) for row in data]
        counts = [row[1] for row in data]

        hour_counts = [0] * 24
        for hour, count in zip(hours, counts):
            hour_counts[hour] = count

        fig, ax = plt.subplots(figsize=(14, 6))
        bars = ax.bar(range(24), hour_counts, color='#ff6b6b', edgecolor='white', linewidth=1.5)

        max_count = max(hour_counts) if hour_counts else 1
        for i, count in enumerate(hour_counts):
            if count == max_count and max_count > 0:
                bars[i].set_color('#00ff88')

        ax.set_xlabel('Hour of Day (24h)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Memories Created', fontsize=12, fontweight='bold')
        ax.set_title('Activity by Hour', fontsize=16, fontweight='bold')
        ax.set_xticks(range(0, 24, 3))
        ax.set_xticklabels([f'{h:02d}:00' for h in range(0, 24, 3)])
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = CHARTS_DIR / f"hourly_{timestamp}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        return output_file

    def generate_full_dashboard(self, days=30):
        """Generate all charts"""
        self.log("=" * 60)
        self.log("GENERATING DASHBOARD")
        self.log("=" * 60)

        try:
            charts = {}

            self.log("📊 Generating activity timeline...")
            charts['timeline'] = str(self.plot_activity_timeline(days))

            self.log("📊 Generating namespace distribution...")
            charts['namespaces'] = str(self.plot_namespace_distribution())

            self.log("📊 Generating hourly activity...")
            charts['hourly'] = str(self.plot_hourly_heatmap())

            self.log("=" * 60)
            self.log("DASHBOARD COMPLETE")
            self.log("=" * 60)

            # Create HTML dashboard
            html_file = self.create_html_dashboard(charts)

            result = {
                "success": True,
                "message": "Dashboard generated successfully",
                "charts": charts,
                "html_dashboard": str(html_file),
                "charts_dir": str(CHARTS_DIR),
                "generated_at": datetime.now().isoformat()
            }

            if self.json_output:
                print(json.dumps(result, indent=2))

            return result

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "message": f"Dashboard generation failed: {e}"
            }

            if self.json_output:
                print(json.dumps(error_result, indent=2))

            return error_result

    def create_html_dashboard(self, charts):
        """Create HTML with Wolf logo"""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Wolf AI Performance Dashboard</title>
    <style>
        body {{
            background: #1a1a1a;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        .logo {{
            width: 200px;
            height: 200px;
            margin: 0 auto 20px;
            display: block;
        }}
        h1 {{
            color: #ff0000;
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px #000000, -1px -1px 2px #000000;
            font-weight: bold;
        }}
        .timestamp {{
            text-align: center;
            color: #888;
            margin-bottom: 40px;
        }}
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .chart-card {{
            background: #2a2a2a;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #333;
        }}
        .chart-card img {{
            width: 100%;
            border-radius: 5px;
        }}
        .chart-title {{
            color: #ff0000;
            text-shadow: 1px 1px 3px #000000;
            font-size: 1.5em;
            margin-bottom: 15px;
            text-align: center;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="header">
        <img src="wolf-logo.png" alt="Wolf AI Enterprises" class="logo">
        <h1>WOLF AI PERFORMANCE DASHBOARD</h1>
    </div>
    <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>

    <div class="chart-grid">
        <div class="chart-card">
            <div class="chart-title">Activity Timeline</div>
            <img src="{Path(charts['timeline']).name}" alt="Timeline">
        </div>
        <div class="chart-card">
            <div class="chart-title">Namespace Distribution</div>
            <img src="{Path(charts['namespaces']).name}" alt="Namespaces">
        </div>
        <div class="chart-card">
            <div class="chart-title">Hourly Activity</div>
            <img src="{Path(charts['hourly']).name}" alt="Hourly">
        </div>
    </div>
</body>
</html>
"""
        output_file = CHARTS_DIR / "dashboard.html"
        with open(output_file, 'w') as f:
            f.write(html)

        return output_file


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Visual Dashboard Generator')
    parser.add_argument('--days', type=int, default=30, help='Days of data to analyze')
    parser.add_argument('--json', action='store_true', help='Output JSON for API integration')

    args = parser.parse_args()

    dashboard = VisualDashboard(json_output=args.json)

    if not dashboard.connect():
        sys.exit(1)

    try:
        result = dashboard.generate_full_dashboard(days=args.days)
        sys.exit(0 if result.get("success", False) else 1)
    finally:
        dashboard.close()


if __name__ == "__main__":
    main()
