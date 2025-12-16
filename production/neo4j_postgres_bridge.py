#!/usr/bin/env python3
"""
Neo4j <-> Postgres Bridge
Connects Neo4j graph to Postgres tables
"""

import psycopg2
from neo4j import GraphDatabase
import os
import json

# Config
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:8687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "wolflogic2024")

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5433"))
PG_USER = os.getenv("PG_USER", "wolf")
PG_PASSWORD = os.getenv("PG_PASSWORD", "wolflogic2024")
PG_DATABASE = os.getenv("PG_DATABASE", "wolf_logic")


class Neo4jPostgresBridge:
    def __init__(self):
        self.neo4j_driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        self.pg_conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            database=PG_DATABASE
        )
        print(f"Connected to Neo4j: {NEO4J_URI}")
        print(f"Connected to Postgres: {PG_HOST}:{PG_PORT}/{PG_DATABASE}")

    def sync_memories_to_neo4j(self):
        """Sync Postgres memories table to Neo4j"""
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT id, content, metadata, namespace, created_at
            FROM memories
            ORDER BY created_at DESC
        """)

        with self.neo4j_driver.session() as session:
            count = 0
            for row in cursor.fetchall():
                memory_id, content, metadata, namespace, created_at = row

                # Create or merge memory node
                session.run("""
                    MERGE (m:Memory {id: $id})
                    SET m.content = $content,
                        m.namespace = $namespace,
                        m.created_at = $created_at,
                        m.metadata = $metadata
                    RETURN m
                """, {
                    "id": memory_id,
                    "content": content,
                    "namespace": namespace,
                    "created_at": created_at.isoformat() if created_at else None,
                    "metadata": json.dumps(metadata) if metadata else None
                })
                count += 1

        cursor.close()
        print(f"Synced {count} memories to Neo4j")
        return count

    def sync_applications_to_neo4j(self):
        """Sync job applications to Neo4j"""
        cursor = self.pg_conn.cursor()
        cursor.execute("""
            SELECT id, position_title, company_name, date_applied,
                   resume_version, job_url, email_sent, call_made,
                   response_received, interview_scheduled, notes
            FROM job_applications
            ORDER BY date_applied DESC
        """)

        with self.neo4j_driver.session() as session:
            count = 0
            for row in cursor.fetchall():
                (app_id, title, company, app_date, resume_ver, url,
                 email_sent, call_made, response_received,
                 interview_scheduled, notes) = row

                # Create application node
                session.run("""
                    MERGE (a:Application {id: $id})
                    SET a.position_title = $title,
                        a.company_name = $company,
                        a.date_applied = $app_date,
                        a.resume_version = $resume_ver,
                        a.job_url = $url,
                        a.email_sent = $email_sent,
                        a.call_made = $call_made,
                        a.response_received = $response_received,
                        a.interview_scheduled = $interview_scheduled,
                        a.notes = $notes

                    MERGE (c:Company {name: $company})
                    MERGE (a)-[:APPLIED_TO]->(c)

                    RETURN a
                """, {
                    "id": app_id,
                    "title": title,
                    "company": company,
                    "app_date": app_date.isoformat() if app_date else None,
                    "resume_ver": resume_ver,
                    "url": url,
                    "email_sent": email_sent,
                    "call_made": call_made,
                    "response_received": response_received,
                    "interview_scheduled": interview_scheduled,
                    "notes": notes
                })
                count += 1

        cursor.close()
        print(f"Synced {count} applications to Neo4j")
        return count

    def query_neo4j_to_postgres(self, cypher_query, table_name, columns):
        """Run Cypher query and store results in Postgres table"""
        with self.neo4j_driver.session() as session:
            result = session.run(cypher_query)
            records = [dict(record) for record in result]

        if not records:
            print("No results from Neo4j")
            return 0

        # Insert into Postgres
        cursor = self.pg_conn.cursor()

        # Build insert statement
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        count = 0
        for record in records:
            values = [record.get(col) for col in columns]
            cursor.execute(insert_sql, values)
            count += 1

        self.pg_conn.commit()
        cursor.close()
        print(f"Inserted {count} records into {table_name}")
        return count

    def get_graph_stats(self):
        """Get Neo4j graph statistics"""
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as label, count(*) as count
            """)
            stats = {record["label"][0]: record["count"] for record in result if record["label"]}
        return stats

    def close(self):
        """Close connections"""
        self.neo4j_driver.close()
        self.pg_conn.close()


def main():
    """Main sync operation"""
    bridge = Neo4jPostgresBridge()

    print("\n=== Syncing Postgres -> Neo4j ===")
    memories_count = bridge.sync_memories_to_neo4j()
    apps_count = bridge.sync_applications_to_neo4j()

    print(f"\n=== Sync Complete ===")
    print(f"Memories: {memories_count}")
    print(f"Applications: {apps_count}")

    print("\n=== Neo4j Graph Stats ===")
    stats = bridge.get_graph_stats()
    for label, count in stats.items():
        print(f"{label}: {count} nodes")

    bridge.close()


if __name__ == "__main__":
    main()
