#!/usr/bin/env python3
"""
Visual Performance Dashboard
Generates actual graphs and charts - no text, all visuals.

For visual learners. Numbers tell the story, pictures make it stick.

Union Way: Show, don't tell.
"""

import json
import psycopg2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import pandas as pd

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
    """Generate visual charts and graphs"""

    def __init__(self):
        self.conn = None
        plt.style.use('dark_background')  # Dark theme for graphs

    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**PG_CONFIG)

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

    def get_agent_totals(self):
        """Get total memories per agent"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, COUNT(*) as count
                FROM memories
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT 10
            """)

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
                LIMIT 15
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
        """Line chart: memory creation over time by agent"""
        data = self.get_activity_timeline(days)

        # Group by agent
        agents = defaultdict(lambda: defaultdict(int))
        for date, user_id, count in data:
            agents[user_id][date] = count

        # Create figure
        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot each agent
        for agent_id, dates in agents.items():
            sorted_dates = sorted(dates.keys())
            counts = [dates[d] for d in sorted_dates]
            ax.plot(sorted_dates, counts, marker='o', label=agent_id, linewidth=2)

        ax.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax.set_ylabel('Memories Created', fontsize=12, fontweight='bold')
        ax.set_title(f'Agent Activity Timeline (Last {days} Days)', fontsize=16, fontweight='bold')
        ax.legend(loc='upper left', framealpha=0.9)
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
        plt.xticks(rotation=45)

        plt.tight_layout()

        output_file = CHARTS_DIR / f"timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        return output_file

    def plot_agent_totals(self):
        """Bar chart: total memories per agent"""
        data = self.get_agent_totals()
        agents = [row[0] for row in data]
        counts = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(12, 7))

        bars = ax.barh(agents, counts, color='#00ff88', edgecolor='white', linewidth=1.5)

        # Add value labels
        for i, (agent, count) in enumerate(zip(agents, counts)):
            ax.text(count + max(counts)*0.01, i, f'{count:,}',
                   va='center', fontsize=11, fontweight='bold')

        ax.set_xlabel('Total Memories', fontsize=12, fontweight='bold')
        ax.set_title('Agent Performance - Total Memories', fontsize=16, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        output_file = CHARTS_DIR / f"agent_totals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        return output_file

    def plot_namespace_distribution(self):
        """Pie chart: namespace distribution"""
        data = self.get_namespace_distribution()
        namespaces = [row[0] for row in data]
        counts = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(12, 8))

        # Color palette
        colors = plt.cm.Set3(range(len(namespaces)))

        wedges, texts, autotexts = ax.pie(
            counts,
            labels=namespaces,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors,
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )

        # Make percentage text white
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

        ax.set_title('Memory Distribution by Namespace', fontsize=16, fontweight='bold', pad=20)

        plt.tight_layout()

        output_file = CHARTS_DIR / f"namespaces_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        return output_file

    def plot_hourly_heatmap(self):
        """Bar chart: activity by hour of day"""
        data = self.get_hourly_activity()
        hours = [int(row[0]) for row in data]
        counts = [row[1] for row in data]

        # Fill in missing hours with 0
        hour_counts = [0] * 24
        for hour, count in zip(hours, counts):
            hour_counts[hour] = count

        fig, ax = plt.subplots(figsize=(14, 6))

        bars = ax.bar(range(24), hour_counts, color='#ff6b6b', edgecolor='white', linewidth=1.5)

        # Highlight peak hours
        max_count = max(hour_counts)
        for i, count in enumerate(hour_counts):
            if count == max_count:
                bars[i].set_color('#00ff88')

        ax.set_xlabel('Hour of Day (24h)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Memories Created', fontsize=12, fontweight='bold')
        ax.set_title('Activity Heatmap - By Hour of Day', fontsize=16, fontweight='bold')
        ax.set_xticks(range(24))
        ax.set_xticklabels([f'{h:02d}:00' for h in range(24)], rotation=45)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        output_file = CHARTS_DIR / f"hourly_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

        return output_file

    def generate_full_dashboard(self, days=30):
        """Generate all charts"""
        print("=" * 60)
        print("GENERATING VISUAL DASHBOARD")
        print("=" * 60)
        print()

        charts = {}

        print("📊 Generating activity timeline...")
        charts['timeline'] = self.plot_activity_timeline(days)
        print(f"   ✓ Saved: {charts['timeline']}")

        print("📊 Generating agent totals...")
        charts['totals'] = self.plot_agent_totals()
        print(f"   ✓ Saved: {charts['totals']}")

        print("📊 Generating namespace distribution...")
        charts['namespaces'] = self.plot_namespace_distribution()
        print(f"   ✓ Saved: {charts['namespaces']}")

        print("📊 Generating hourly heatmap...")
        charts['hourly'] = self.plot_hourly_heatmap()
        print(f"   ✓ Saved: {charts['hourly']}")

        print()
        print("=" * 60)
        print("DASHBOARD COMPLETE")
        print("=" * 60)
        print(f"Charts saved to: {CHARTS_DIR}")
        print()
        print("CHARTS GENERATED:")
        for name, path in charts.items():
            print(f"  • {name}: {path.name}")
        print()

        return charts

    def create_html_dashboard(self, charts):
        """Create HTML page with all charts"""
        html = f"""
<!DOCTYPE html>
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
        h1 {{
            text-align: center;
            color: #00ff88;
            font-size: 3em;
            margin-bottom: 10px;
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
        }}
        .chart-card img {{
            width: 100%;
            border-radius: 5px;
        }}
        .chart-title {{
            color: #00ff88;
            font-size: 1.5em;
            margin-bottom: 15px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>🚀 Wolf AI Performance Dashboard</h1>
    <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>

    <div class="chart-grid">
        <div class="chart-card">
            <div class="chart-title">Activity Timeline</div>
            <img src="{charts['timeline'].name}" alt="Timeline">
        </div>
        <div class="chart-card">
            <div class="chart-title">Agent Performance</div>
            <img src="{charts['totals'].name}" alt="Totals">
        </div>
        <div class="chart-card">
            <div class="chart-title">Namespace Distribution</div>
            <img src="{charts['namespaces'].name}" alt="Namespaces">
        </div>
        <div class="chart-card">
            <div class="chart-title">Hourly Activity</div>
            <img src="{charts['hourly'].name}" alt="Hourly">
        </div>
    </div>
</body>
</html>
"""
        output_file = CHARTS_DIR / "dashboard.html"
        with open(output_file, 'w') as f:
            f.write(html)

        print(f"HTML Dashboard: {output_file}")
        print(f"Open in browser: file://{output_file.absolute()}")

        return output_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Visual Performance Dashboard')
    parser.add_argument('--days', type=int, default=30, help='Days of data to analyze')

    args = parser.parse_args()

    dashboard = VisualDashboard()

    try:
        dashboard.connect()
        charts = dashboard.generate_full_dashboard(days=args.days)
        html_file = dashboard.create_html_dashboard(charts)

        print("\n✓ Open the HTML file in your browser to view all charts.")

    finally:
        dashboard.close()
