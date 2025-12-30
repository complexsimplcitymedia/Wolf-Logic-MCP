#!/usr/bin/env python3
"""
Agent Performance Dashboard
Real-time monitoring of AI agent efficiency, learning curves, and competence.

Tracks:
- Model efficiency (tokens, success rates, patterns)
- Performance over time (are they improving?)
- Query patterns and database readiness
- Resource utilization

Union Way: Measure everything. Trust nothing. Improve continuously.
"""

import json
import psycopg2
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Database
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Metrics storage
METRICS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/metrics/data")
METRICS_DIR.mkdir(parents=True, exist_ok=True)


class AgentPerformanceDashboard:
    """Monitor and visualize agent performance metrics"""

    def __init__(self):
        self.conn = None
        self.metrics = {
            "agents": {},
            "timestamp": datetime.now().isoformat(),
            "summary": {}
        }

    def connect(self):
        """Connect to database"""
        self.conn = psycopg2.connect(**PG_CONFIG)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_agent_activity(self, days=7):
        """Get agent activity stats for past N days"""
        cutoff = datetime.now() - timedelta(days=days)

        with self.conn.cursor() as cur:
            # Memory creation by agent
            cur.execute("""
                SELECT
                    user_id,
                    COUNT(*) as memory_count,
                    AVG(LENGTH(content)) as avg_content_length,
                    MIN(created_at) as first_activity,
                    MAX(created_at) as last_activity
                FROM memories
                WHERE created_at > %s
                GROUP BY user_id
                ORDER BY memory_count DESC
            """, (cutoff,))

            results = cur.fetchall()

            agents = {}
            for user_id, count, avg_len, first, last in results:
                # Calculate activity span
                if first and last:
                    span = (last - first).total_seconds() / 3600  # hours
                    rate = count / span if span > 0 else 0
                else:
                    span = 0
                    rate = 0

                agents[user_id] = {
                    "memory_count": count,
                    "avg_content_length": round(float(avg_len), 2) if avg_len else 0,
                    "first_activity": first.isoformat() if first else None,
                    "last_activity": last.isoformat() if last else None,
                    "active_hours": round(span, 2),
                    "memories_per_hour": round(rate, 2)
                }

            return agents

    def get_memory_type_distribution(self):
        """Get distribution of memory types"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT memory_type, COUNT(*) as count
                FROM memories
                GROUP BY memory_type
                ORDER BY count DESC
            """)

            return dict(cur.fetchall())

    def get_namespace_stats(self):
        """Get namespace statistics"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT
                    namespace,
                    COUNT(*) as memory_count,
                    COUNT(DISTINCT user_id) as agent_count,
                    MAX(created_at) as latest_update
                FROM memories
                WHERE namespace IS NOT NULL
                GROUP BY namespace
                ORDER BY memory_count DESC
            """)

            namespaces = {}
            for ns, count, agents, latest in cur.fetchall():
                namespaces[ns] = {
                    "memory_count": count,
                    "agent_count": agents,
                    "latest_update": latest.isoformat() if latest else None
                }

            return namespaces

    def get_trend_data(self, days=30):
        """Get performance trends over time"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT
                    DATE(created_at) as date,
                    user_id,
                    COUNT(*) as memories
                FROM memories
                WHERE created_at > NOW() - INTERVAL '%s days'
                GROUP BY DATE(created_at), user_id
                ORDER BY date DESC, memories DESC
            """, (days,))

            trends = defaultdict(lambda: defaultdict(int))
            for date, user_id, count in cur.fetchall():
                trends[str(date)][user_id] = count

            return dict(trends)

    def calculate_agent_scores(self, agents):
        """Calculate performance scores for each agent"""
        scores = {}

        for agent_id, stats in agents.items():
            # Score components
            activity_score = min(stats["memories_per_hour"] * 10, 100)  # Cap at 100
            content_score = min(stats["avg_content_length"] / 10, 100)  # Longer = better (to a point)
            consistency_score = min(stats["active_hours"] * 2, 100)  # More consistent = better

            # Overall score (weighted average)
            overall = (activity_score * 0.4 + content_score * 0.3 + consistency_score * 0.3)

            scores[agent_id] = {
                "activity_score": round(activity_score, 2),
                "content_score": round(content_score, 2),
                "consistency_score": round(consistency_score, 2),
                "overall_score": round(overall, 2)
            }

        return scores

    def generate_dashboard(self, days=7):
        """Generate complete dashboard"""
        print("=" * 80)
        print("AGENT PERFORMANCE DASHBOARD")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Analysis period: Last {days} days")
        print("=" * 80)
        print()

        # Get data
        agents = self.get_agent_activity(days)
        memory_types = self.get_memory_type_distribution()
        namespaces = self.get_namespace_stats()
        scores = self.calculate_agent_scores(agents)

        # Agent summary table
        print("AGENT ACTIVITY SUMMARY:")
        print(f"{'Agent':<20} | {'Memories':<10} | {'Mem/Hour':<10} | {'Avg Length':<12} | {'Score':<8}")
        print("-" * 80)

        for agent_id in sorted(agents.keys(), key=lambda x: agents[x]["memory_count"], reverse=True):
            stats = agents[agent_id]
            score = scores.get(agent_id, {}).get("overall_score", 0)

            print(f"{agent_id:<20} | {stats['memory_count']:<10} | "
                  f"{stats['memories_per_hour']:<10.2f} | {stats['avg_content_length']:<12.2f} | "
                  f"{score:<8.2f}")

        print()

        # Memory type distribution
        print("MEMORY TYPE DISTRIBUTION:")
        total_memories = sum(memory_types.values())
        for mem_type, count in sorted(memory_types.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_memories * 100) if total_memories > 0 else 0
            bar_len = int(pct / 2)  # 50 char max
            bar = "█" * bar_len
            print(f"  {mem_type:<20} [{bar:<50}] {count:>6} ({pct:>5.1f}%)")

        print()

        # Namespace stats
        print("NAMESPACE ACTIVITY:")
        print(f"{'Namespace':<30} | {'Memories':<10} | {'Agents':<8} | {'Latest Update':<20}")
        print("-" * 80)

        for ns, stats in sorted(namespaces.items(), key=lambda x: x[1]["memory_count"], reverse=True):
            latest = stats["latest_update"][:19] if stats["latest_update"] else "N/A"
            print(f"{ns:<30} | {stats['memory_count']:<10} | {stats['agent_count']:<8} | {latest:<20}")

        print()

        # Performance scores
        print("AGENT PERFORMANCE SCORES:")
        print(f"{'Agent':<20} | {'Activity':<10} | {'Content':<10} | {'Consistency':<12} | {'Overall':<10}")
        print("-" * 80)

        for agent_id in sorted(scores.keys(), key=lambda x: scores[x]["overall_score"], reverse=True):
            s = scores[agent_id]
            print(f"{agent_id:<20} | {s['activity_score']:<10.2f} | "
                  f"{s['content_score']:<10.2f} | {s['consistency_score']:<12.2f} | "
                  f"{s['overall_score']:<10.2f}")

        print()
        print("=" * 80)

        # Store metrics
        self.metrics["agents"] = agents
        self.metrics["scores"] = scores
        self.metrics["memory_types"] = memory_types
        self.metrics["namespaces"] = namespaces

        return self.metrics

    def save_metrics(self):
        """Save metrics to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = METRICS_DIR / f"agent_metrics_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

        print(f"Metrics saved to: {output_file}")
        return output_file

    def compare_to_baseline(self, baseline_file):
        """Compare current metrics to baseline"""
        if not Path(baseline_file).exists():
            print(f"Baseline file not found: {baseline_file}")
            return

        with open(baseline_file, 'r') as f:
            baseline = json.load(f)

        print("\nPERFORMANCE TRENDS (vs baseline):")
        print(f"{'Agent':<20} | {'Score Change':<15} | {'Trend':<10}")
        print("-" * 50)

        for agent_id, current_score in self.metrics.get("scores", {}).items():
            baseline_score = baseline.get("scores", {}).get(agent_id, {})

            if baseline_score:
                current = current_score["overall_score"]
                previous = baseline_score["overall_score"]
                change = current - previous
                trend = "📈 IMPROVING" if change > 0 else "📉 DECLINING" if change < 0 else "→ STABLE"

                print(f"{agent_id:<20} | {change:>+14.2f} | {trend:<10}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Agent Performance Dashboard')
    parser.add_argument('--days', type=int, default=7, help='Number of days to analyze')
    parser.add_argument('--baseline', type=str, help='Baseline file for comparison')
    parser.add_argument('--watch', action='store_true', help='Run continuously (refresh every 60s)')

    args = parser.parse_args()

    dashboard = AgentPerformanceDashboard()

    try:
        dashboard.connect()

        if args.watch:
            import time
            while True:
                dashboard.generate_dashboard(days=args.days)
                dashboard.save_metrics()

                if args.baseline:
                    dashboard.compare_to_baseline(args.baseline)

                print("\nRefreshing in 60 seconds... (Ctrl+C to stop)")
                time.sleep(60)
                print("\033[2J\033[H")  # Clear screen
        else:
            dashboard.generate_dashboard(days=args.days)
            output_file = dashboard.save_metrics()

            if args.baseline:
                dashboard.compare_to_baseline(args.baseline)
            else:
                print(f"\nTip: Save this as baseline: --baseline {output_file}")

    finally:
        dashboard.close()
