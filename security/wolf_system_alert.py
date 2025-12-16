#!/usr/bin/env python3
"""
Wolf System Alert - Emergency Notification System
Sends critical system alerts to librarian (system_announcements namespace)
Location: /mnt/Wolf-code/Wolf-Ai-Enterptises/security/
"""

import psycopg2
import json
import datetime
from typing import Dict, Any

class WolfSystemAlert:
    def __init__(self):
        self.db_config = {
            "host": "localhost",
            "port": 5433,
            "database": "wolf_logic",
            "user": "wolf",
            "password": "wolflogic2024"
        }

    def send_emergency_alert(self, alert_type: str, severity: str, details: Dict[str, Any]):
        """
        Send emergency alert to librarian system_announcements

        Args:
            alert_type: Type of alert (e.g., "SYSTEM_INTEGRITY_BREACH", "ANOMALY_DETECTED")
            severity: "CRITICAL", "HIGH", "MEDIUM", "LOW"
            details: Dict containing alert details
        """

        alert_content = {
            "timestamp": datetime.datetime.now().isoformat(),
            "alert_type": alert_type,
            "severity": severity,
            "details": details,
            "source": "wolf_system_monitor",
            "requires_immediate_attention": severity in ["CRITICAL", "HIGH"]
        }

        # Format as emergency system announcement
        announcement = f"""🚨 SYSTEM ALERT - {severity} 🚨

Type: {alert_type}
Time: {alert_content['timestamp']}
Source: Wolf System Monitor

DETAILS:
{json.dumps(details, indent=2)}

""" + ("=" * 60) + """

This is an automated alert from the Wolf System Integrity Monitor.
All deployed agents should acknowledge this alert.

Investigation required: {alert_content['requires_immediate_attention']}
"""

        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Insert into memories with system_announcements namespace
            insert_query = """
            INSERT INTO memories (user_id, content, namespace, memory_type, metadata)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """

            cursor.execute(insert_query, (
                "wolf_system_monitor",
                announcement,
                "system_announcements",
                "security_alert",
                json.dumps(alert_content)
            ))

            alert_id = cursor.fetchone()[0]
            conn.commit()

            print(f"✅ Emergency alert sent to librarian")
            print(f"   Alert ID: {alert_id}")
            print(f"   Namespace: system_announcements")
            print(f"   Severity: {severity}")

            cursor.close()
            conn.close()

            return alert_id

        except Exception as e:
            print(f"❌ Failed to send emergency alert: {e}")
            # Fallback: Write to local file
            fallback_path = "/mnt/Wolf-code/Wolf-Ai-Enterptises/security/alerts/alert_fallback.log"
            with open(fallback_path, 'a') as f:
                f.write(f"\n{announcement}\n")
            print(f"⚠️  Alert written to fallback log: {fallback_path}")
            return None

    def test_alert_system(self):
        """Test the alert system with a low-severity test message"""
        print("Testing Wolf System Alert...")
        alert_id = self.send_emergency_alert(
            alert_type="SYSTEM_TEST",
            severity="LOW",
            details={
                "message": "This is a test alert from the Wolf System Monitor",
                "test_timestamp": datetime.datetime.now().isoformat(),
                "status": "operational"
            }
        )
        return alert_id

if __name__ == "__main__":
    alerter = WolfSystemAlert()
    alerter.test_alert_system()
