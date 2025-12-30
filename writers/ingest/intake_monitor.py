#!/usr/bin/env python3
"""
Intake Stream Monitor
Uses llama3.2:1b to analyze queue depth, congestion, processing lag
Alerts on bottlenecks before they become critical
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG
# ============================================================================

INTAKE_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/client_dump")
PROCESSED_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/processed_intake")
PGAI_QUEUE = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/pgai_queue")

OLLAMA_BASE = "http://localhost:11434"
MONITOR_MODEL = "llama3.2:1b"
CHECK_INTERVAL = 60  # Check every 60 seconds

# Alert thresholds
INTAKE_QUEUE_WARNING = 50
INTAKE_QUEUE_CRITICAL = 100
PGAI_QUEUE_WARNING = 30
PGAI_QUEUE_CRITICAL = 60
PROCESSING_LAG_WARNING = 300  # 5 minutes
PROCESSING_LAG_CRITICAL = 900  # 15 minutes

# ============================================================================
# METRICS COLLECTION
# ============================================================================

def get_queue_metrics() -> Dict:
    """Collect metrics from all queues"""
    intake_files = list(INTAKE_DIR.glob("*.json"))
    processed_files = list(PROCESSED_DIR.glob("*.json"))
    pgai_files = list(PGAI_QUEUE.glob("pgai_*.json"))
    
    # Calculate processing lag
    oldest_intake = None
    if intake_files:
        oldest_intake = min(f.stat().st_mtime for f in intake_files)
        oldest_age = time.time() - oldest_intake
    else:
        oldest_age = 0
    
    # Files per user in intake queue
    intake_by_user = {}
    for f in intake_files:
        username = f.name.split('_')[0]
        intake_by_user[username] = intake_by_user.get(username, 0) + 1
    
    # Recent throughput (last 5 minutes)
    five_min_ago = time.time() - 300
    recent_processed = len([f for f in processed_files if f.stat().st_mtime > five_min_ago])
    
    return {
        "timestamp": datetime.now().isoformat(),
        "intake_queue": len(intake_files),
        "pgai_queue": len(pgai_files),
        "processed_total": len(processed_files),
        "oldest_unprocessed_age": oldest_age,
        "intake_by_user": intake_by_user,
        "throughput_5min": recent_processed,
        "processing_rate": recent_processed / 5.0 if recent_processed > 0 else 0  # files/min
    }


def check_thresholds(metrics: Dict) -> List[Dict]:
    """Check metrics against thresholds and generate alerts"""
    alerts = []
    
    # Intake queue depth
    if metrics["intake_queue"] >= INTAKE_QUEUE_CRITICAL:
        alerts.append({
            "severity": "critical",
            "type": "intake_queue_depth",
            "message": f"Intake queue critically high: {metrics['intake_queue']} files",
            "value": metrics["intake_queue"]
        })
    elif metrics["intake_queue"] >= INTAKE_QUEUE_WARNING:
        alerts.append({
            "severity": "warning",
            "type": "intake_queue_depth",
            "message": f"Intake queue elevated: {metrics['intake_queue']} files",
            "value": metrics["intake_queue"]
        })
    
    # pgai queue depth
    if metrics["pgai_queue"] >= PGAI_QUEUE_CRITICAL:
        alerts.append({
            "severity": "critical",
            "type": "pgai_queue_depth",
            "message": f"pgai queue critically high: {metrics['pgai_queue']} files",
            "value": metrics["pgai_queue"]
        })
    elif metrics["pgai_queue"] >= PGAI_QUEUE_WARNING:
        alerts.append({
            "severity": "warning",
            "type": "pgai_queue_depth",
            "message": f"pgai queue elevated: {metrics['pgai_queue']} files",
            "value": metrics["pgai_queue"]
        })
    
    # Processing lag
    if metrics["oldest_unprocessed_age"] >= PROCESSING_LAG_CRITICAL:
        alerts.append({
            "severity": "critical",
            "type": "processing_lag",
            "message": f"Oldest file unprocessed for {metrics['oldest_unprocessed_age']/60:.1f} minutes",
            "value": metrics["oldest_unprocessed_age"]
        })
    elif metrics["oldest_unprocessed_age"] >= PROCESSING_LAG_WARNING:
        alerts.append({
            "severity": "warning",
            "type": "processing_lag",
            "message": f"Processing lag detected: {metrics['oldest_unprocessed_age']/60:.1f} minutes",
            "value": metrics["oldest_unprocessed_age"]
        })
    
    # User concentration (potential abuse)
    for user, count in metrics["intake_by_user"].items():
        if count > 30:
            alerts.append({
                "severity": "warning",
                "type": "user_concentration",
                "message": f"High volume from user {user}: {count} files in queue",
                "value": count,
                "user": user
            })
    
    return alerts


# ============================================================================
# LLM ANALYSIS
# ============================================================================

def analyze_with_llm(metrics: Dict, alerts: List[Dict]) -> str:
    """Use llama3.2:1b to analyze queue health and provide recommendations"""
    
    prompt = f"""Analyze this intake stream monitoring data and provide brief recommendations:

METRICS:
- Intake queue: {metrics['intake_queue']} files
- pgai queue: {metrics['pgai_queue']} files
- Processing rate: {metrics['processing_rate']:.2f} files/min
- Oldest unprocessed: {metrics['oldest_unprocessed_age']/60:.1f} minutes
- Recent throughput: {metrics['throughput_5min']} files (last 5 min)

ALERTS: {len(alerts)}
{chr(10).join(f"- [{a['severity'].upper()}] {a['message']}" for a in alerts) if alerts else "None"}

USER DISTRIBUTION:
{chr(10).join(f"- {user}: {count} files" for user, count in metrics['intake_by_user'].items()) if metrics['intake_by_user'] else "No files in queue"}

Provide 2-3 sentence analysis: Is the system healthy? Any bottlenecks? Recommendations?"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={
                "model": MONITOR_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3
            },
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "").strip()
        
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return f"Analysis unavailable: {str(e)}"


# ============================================================================
# MONITORING LOOP
# ============================================================================

def log_status(metrics: Dict, alerts: List[Dict], analysis: str):
    """Log current status to console and file"""
    
    status = {
        "timestamp": metrics["timestamp"],
        "metrics": metrics,
        "alerts": alerts,
        "analysis": analysis
    }
    
    # Console output
    logger.info("=" * 70)
    logger.info(f"INTAKE STREAM MONITOR - {metrics['timestamp']}")
    logger.info(f"Queues: Intake={metrics['intake_queue']} pgai={metrics['pgai_queue']} Processed={metrics['processed_total']}")
    logger.info(f"Rate: {metrics['processing_rate']:.2f} files/min | Lag: {metrics['oldest_unprocessed_age']/60:.1f} min")
    
    if alerts:
        logger.warning(f"ALERTS ({len(alerts)}):")
        for alert in alerts:
            logger.warning(f"  [{alert['severity'].upper()}] {alert['message']}")
    else:
        logger.info("Status: HEALTHY - No alerts")
    
    logger.info(f"Analysis: {analysis}")
    logger.info("=" * 70)
    
    # Write to log file
    log_dir = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"intake_monitor_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(status) + '\n')


def run_monitor():
    """Main monitoring loop"""
    logger.info(f"Starting Intake Stream Monitor")
    logger.info(f"Model: {MONITOR_MODEL}")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    logger.info(f"Monitoring: {INTAKE_DIR}")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # Collect metrics
            metrics = get_queue_metrics()
            
            # Check thresholds
            alerts = check_thresholds(metrics)
            
            # LLM analysis (every 5th iteration to save resources)
            if iteration % 5 == 1:
                analysis = analyze_with_llm(metrics, alerts)
            else:
                analysis = "Skipped (runs every 5 minutes)"
            
            # Log status
            log_status(metrics, alerts, analysis)
            
            # Critical alert - log extra info
            if any(a["severity"] == "critical" for a in alerts):
                logger.critical("CRITICAL CONDITION DETECTED - System may be overloaded!")
            
            # Sleep until next check
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor crashed: {e}", exc_info=True)


# ============================================================================
# STATS COMMAND
# ============================================================================

def print_current_stats():
    """Print current stats and exit"""
    metrics = get_queue_metrics()
    alerts = check_thresholds(metrics)
    analysis = analyze_with_llm(metrics, alerts)
    
    print(json.dumps({
        "metrics": metrics,
        "alerts": alerts,
        "analysis": analysis
    }, indent=2))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print_current_stats()
    else:
        run_monitor()
