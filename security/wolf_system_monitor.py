#!/usr/bin/env python3
"""
Wolf System Monitor - Continuous Integrity Monitoring
Runs in background, compares current state to baseline, sends alerts on anomalies
Location: /mnt/Wolf-code/Wolf-Ai-Enterptises/security/
"""

import os
import sys
import time
import json
import hashlib
import datetime
from pathlib import Path
from baseline_check import collect_baseline
from wolf_system_alert import WolfSystemAlert

class WolfSystemMonitor:
    def __init__(self, baseline_path: str, check_interval: int = 300):
        """
        Initialize system monitor

        Args:
            baseline_path: Path to reference baseline JSON
            check_interval: Seconds between checks (default: 300 = 5 minutes)
        """
        self.baseline_path = Path(baseline_path)
        self.check_interval = check_interval
        self.alerter = WolfSystemAlert()
        self.baseline = None
        self.check_count = 0
        self.alert_count = 0

        # Load baseline
        self.load_baseline()

    def load_baseline(self):
        """Load reference baseline from file"""
        if not self.baseline_path.exists():
            raise FileNotFoundError(f"Baseline not found: {self.baseline_path}")

        with open(self.baseline_path) as f:
            self.baseline = json.load(f)

        print(f"✅ Loaded baseline: {self.baseline_path}")
        print(f"   Baseline hash: {self.baseline.get('baseline_hash')}")
        print(f"   Collection time: {self.baseline.get('collection_time')}")
        print(f"   Total checks: {len(self.baseline.get('checks', {}))}")

    def compare_to_baseline(self, current_state):
        """
        Compare current system state to baseline

        Returns:
            Dict with differences and severity assessment
        """
        differences = []
        severity = "LOW"

        for check_name, check_data in current_state["checks"].items():
            if check_name not in self.baseline["checks"]:
                differences.append({
                    "check": check_name,
                    "type": "NEW_CHECK",
                    "severity": "MEDIUM",
                    "details": "Check not in baseline"
                })
                continue

            baseline_check = self.baseline["checks"][check_name]
            current_stdout = check_data.get("stdout", "")
            baseline_stdout = baseline_check.get("stdout", "")

            # Skip timestamp-sensitive checks
            if check_name in ["memory_usage", "disk_io", "process_counts"]:
                continue

            # Check for differences
            if current_stdout != baseline_stdout:
                diff_type = self._classify_difference(check_name, current_stdout, baseline_stdout)
                diff_severity = self._assess_severity(check_name, diff_type)

                differences.append({
                    "check": check_name,
                    "type": diff_type,
                    "severity": diff_severity,
                    "baseline_length": len(baseline_stdout),
                    "current_length": len(current_stdout),
                    "details": f"Output changed in {check_name}"
                })

                # Escalate severity if needed
                if diff_severity == "CRITICAL" and severity != "CRITICAL":
                    severity = "CRITICAL"
                elif diff_severity == "HIGH" and severity not in ["CRITICAL", "HIGH"]:
                    severity = "HIGH"
                elif diff_severity == "MEDIUM" and severity == "LOW":
                    severity = "MEDIUM"

        return {
            "differences_count": len(differences),
            "differences": differences,
            "severity": severity,
            "timestamp": datetime.datetime.now().isoformat()
        }

    def _classify_difference(self, check_name, current, baseline):
        """Classify the type of difference detected"""
        # Docker container changes
        if "docker_containers" in check_name:
            if len(current) < len(baseline):
                return "CONTAINER_STOPPED"
            elif len(current) > len(baseline):
                return "CONTAINER_ADDED"
            else:
                return "CONTAINER_MODIFIED"

        # Service changes
        if "systemd_services" in check_name:
            if len(current) < len(baseline):
                return "SERVICE_STOPPED"
            elif len(current) > len(baseline):
                return "SERVICE_STARTED"
            else:
                return "SERVICE_MODIFIED"

        # Database changes
        if "postgres" in check_name or "neo4j" in check_name:
            return "DATABASE_CHANGE"

        # Network changes
        if "network" in check_name:
            return "NETWORK_CHANGE"

        # Filesystem changes
        if "filesystem" in check_name or "directories" in check_name:
            return "FILESYSTEM_CHANGE"

        return "UNKNOWN_CHANGE"

    def _assess_severity(self, check_name, diff_type):
        """Assess severity of detected difference"""
        # Critical severities
        if diff_type in ["SERVICE_STOPPED", "CONTAINER_STOPPED"]:
            # Critical services/containers
            critical_items = ["postgres", "neo4j", "docker", "tailscale"]
            if any(item in check_name for item in critical_items):
                return "CRITICAL"
            return "HIGH"

        if diff_type == "NETWORK_CHANGE":
            return "HIGH"

        if diff_type == "DATABASE_CHANGE":
            return "MEDIUM"

        if diff_type in ["SERVICE_STARTED", "CONTAINER_ADDED"]:
            return "MEDIUM"  # New services/containers warrant investigation

        if diff_type == "FILESYSTEM_CHANGE":
            return "MEDIUM"

        return "LOW"

    def run_check(self):
        """Run a single monitoring check"""
        # GPU collision avoidance
        from gpu_check import safe_to_run_monitor

        safe, reason, vram = safe_to_run_monitor()
        if not safe:
            print(f"⏸️  SKIPPING CHECK - {reason}")
            print(f"   Will retry next interval...")
            return None

        self.check_count += 1
        print(f"\n{'='*60}")
        print(f"Wolf System Monitor - Check #{self.check_count}")
        print(f"Time: {datetime.datetime.now().isoformat()}")
        print(f"GPU Status: {reason}")
        print(f"{'='*60}\n")

        # Collect current system state
        current_state = collect_baseline()

        # Compare to baseline
        comparison = self.compare_to_baseline(current_state)

        print(f"Differences detected: {comparison['differences_count']}")
        print(f"Severity: {comparison['severity']}")

        # Send alert if differences found
        if comparison['differences_count'] > 0 and comparison['severity'] in ["CRITICAL", "HIGH", "MEDIUM"]:
            self.alert_count += 1
            print(f"\n🚨 SENDING ALERT (Alert #{self.alert_count})")

            alert_id = self.alerter.send_emergency_alert(
                alert_type="SYSTEM_INTEGRITY_ANOMALY",
                severity=comparison['severity'],
                details={
                    "check_number": self.check_count,
                    "differences_count": comparison['differences_count'],
                    "differences": comparison['differences'],
                    "comparison_time": comparison['timestamp'],
                    "baseline_file": str(self.baseline_path)
                }
            )

            print(f"Alert ID: {alert_id}")
        else:
            print("✅ System state matches baseline - No alerts")

        return comparison

    def run_continuous(self):
        """Run monitoring loop continuously"""
        print(f"\n{'='*60}")
        print("WOLF SYSTEM MONITOR - STARTING")
        print(f"{'='*60}")
        print(f"Baseline: {self.baseline_path}")
        print(f"Check interval: {self.check_interval} seconds ({self.check_interval/60:.1f} minutes)")
        print(f"Started: {datetime.datetime.now().isoformat()}")
        print(f"{'='*60}\n")

        try:
            while True:
                self.run_check()
                print(f"\nNext check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print(f"\n\n{'='*60}")
            print("WOLF SYSTEM MONITOR - SHUTDOWN")
            print(f"{'='*60}")
            print(f"Total checks: {self.check_count}")
            print(f"Total alerts: {self.alert_count}")
            print(f"Stopped: {datetime.datetime.now().isoformat()}")
            print(f"{'='*60}\n")
            sys.exit(0)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Wolf System Integrity Monitor")
    parser.add_argument(
        "--baseline",
        required=True,
        help="Path to baseline JSON file"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Check interval in seconds (default: 300)"
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Run single check and exit (no continuous monitoring)"
    )

    args = parser.parse_args()

    # Activate messiah environment
    os.environ["PATH"] = f"/home/thewolfwalksalone/anaconda3/envs/messiah/bin:{os.environ['PATH']}"

    monitor = WolfSystemMonitor(
        baseline_path=args.baseline,
        check_interval=args.interval
    )

    if args.single:
        monitor.run_check()
    else:
        monitor.run_continuous()
