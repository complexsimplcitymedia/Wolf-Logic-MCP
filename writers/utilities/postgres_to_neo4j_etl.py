#!/usr/bin/env python3
"""
PostgreSQL → Neo4j ETL Pipeline
Extracts memories from wolf_logic, builds graph in Neo4j.

Graph Structure:
- Nodes: Memory, User, Namespace, Tag
- Edges: CREATED_BY, BELONGS_TO, TAGGED_WITH, RELATED_TO (via embeddings)

Union Way: Extract, transform, load. No shortcuts.
"""

import json
import psycopg2
from neo4j import GraphDatabase
from datetime import datetime

# Database configs
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

NEO4J_CONFIG = {
    "uri": "bolt://localhost:8687",
    "user": "neo4j",
    "password": "wolflogic2024"
}


class MemoryGraphBuilder:
    """Build knowledge graph from PostgreSQL memories"""

    def __init__(self):
        self.pg_conn = None
        self.neo4j_driver = None
        self.stats = {
            "memories_processed": 0,
            "nodes_created": 0,
            "relationships_created": 0,
            "errors": 0
        }

    def connect(self):
        """Connect to both databases"""
        print("Connecting to PostgreSQL...")
        self.pg_conn = psycopg2.connect(**PG_CONFIG)

        print("Connecting to Neo4j...")
        self.neo4j_driver = GraphDatabase.driver(
            NEO4J_CONFIG["uri"],
            auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"])
        )

        print("Connected to both databases.\n")

    def close(self):
        """Close all connections"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()

    def setup_neo4j_schema(self):
        """Create indexes and constraints in Neo4j"""
        print("Setting up Neo4j schema...")

        with self.neo4j_driver.session() as session:
            # Constraints (unique IDs)
            session.run("CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE")
            session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT namespace_name IF NOT EXISTS FOR (n:Namespace) REQUIRE n.name IS UNIQUE")

            # Indexes for fast lookups
            session.run("CREATE INDEX memory_created IF NOT EXISTS FOR (m:Memory) ON (m.created_at)")
            session.run("CREATE INDEX memory_type IF NOT EXISTS FOR (m:Memory) ON (m.memory_type)")

        print("Neo4j schema ready.\n")

    def fetch_memories_batch(self, offset, limit=1000):
        """Fetch batch of memories from PostgreSQL"""
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                SELECT id, user_id, content, metadata, memory_type, namespace, created_at, updated_at
                FROM memories
                ORDER BY id
                LIMIT %s OFFSET %s
            """, (limit, offset))

            return cur.fetchall()

    def create_memory_node(self, session, memory):
        """Create Memory node and relationships in Neo4j"""
        memory_id, user_id, content, metadata, memory_type, namespace, created_at, updated_at = memory

        # Parse metadata if JSON
        metadata_dict = {}
        if metadata:
            try:
                metadata_dict = json.loads(metadata) if isinstance(metadata, str) else metadata
            except:
                pass

        # Create Memory node
        session.run("""
            MERGE (m:Memory {id: $id})
            SET m.content = $content,
                m.memory_type = $memory_type,
                m.created_at = $created_at,
                m.updated_at = $updated_at,
                m.metadata = $metadata
        """, {
            "id": str(memory_id),
            "content": content,
            "memory_type": memory_type,
            "created_at": created_at.isoformat() if created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else None,
            "metadata": json.dumps(metadata_dict)
        })
        self.stats["nodes_created"] += 1

        # Create User node and relationship
        if user_id:
            session.run("""
                MERGE (u:User {id: $user_id})
                WITH u
                MATCH (m:Memory {id: $memory_id})
                MERGE (u)-[:CREATED]->(m)
            """, {"user_id": user_id, "memory_id": str(memory_id)})
            self.stats["relationships_created"] += 1

        # Create Namespace node and relationship
        if namespace:
            session.run("""
                MERGE (n:Namespace {name: $namespace})
                WITH n
                MATCH (m:Memory {id: $memory_id})
                MERGE (m)-[:BELONGS_TO]->(n)
            """, {"namespace": namespace, "memory_id": str(memory_id)})
            self.stats["relationships_created"] += 1

        # Extract and create tags if in metadata
        tags = metadata_dict.get('tags', [])
        if isinstance(tags, list):
            for tag in tags:
                session.run("""
                    MERGE (t:Tag {name: $tag})
                    WITH t
                    MATCH (m:Memory {id: $memory_id})
                    MERGE (m)-[:TAGGED_WITH]->(t)
                """, {"tag": str(tag), "memory_id": str(memory_id)})
                self.stats["relationships_created"] += 1

    def process_memories(self, batch_size=1000):
        """Process all memories from PostgreSQL into Neo4j"""
        print("Starting ETL pipeline...")
        print(f"Batch size: {batch_size}\n")

        offset = 0
        batch_num = 1

        while True:
            print(f"Processing batch #{batch_num} (offset: {offset})...")

            memories = self.fetch_memories_batch(offset, batch_size)

            if not memories:
                print("No more memories to process.")
                break

            # Process batch
            with self.neo4j_driver.session() as session:
                for memory in memories:
                    try:
                        self.create_memory_node(session, memory)
                        self.stats["memories_processed"] += 1
                    except Exception as e:
                        print(f"Error processing memory {memory[0]}: {e}")
                        self.stats["errors"] += 1

            print(f"  Processed: {len(memories)} memories")
            print(f"  Total processed: {self.stats['memories_processed']}")
            print(f"  Nodes created: {self.stats['nodes_created']}")
            print(f"  Relationships: {self.stats['relationships_created']}")
            print(f"  Errors: {self.stats['errors']}\n")

            offset += batch_size
            batch_num += 1

    def build_similarity_edges(self, similarity_threshold=0.7, limit=100):
        """
        Build RELATED_TO edges based on embedding similarity.
        Uses PostgreSQL vector similarity to find related memories.
        """
        print(f"Building similarity edges (threshold: {similarity_threshold})...")

        with self.pg_conn.cursor() as cur:
            # Get memories with embeddings
            cur.execute("""
                SELECT m1.id, m2.id, 1 - (m1.embedding <=> m2.embedding) as similarity
                FROM memories m1
                CROSS JOIN LATERAL (
                    SELECT id, embedding
                    FROM memories m2
                    WHERE m2.id != m1.id
                    AND m2.embedding IS NOT NULL
                    ORDER BY m1.embedding <=> m2.embedding
                    LIMIT 5
                ) m2
                WHERE m1.embedding IS NOT NULL
                AND 1 - (m1.embedding <=> m2.embedding) > %s
                LIMIT %s
            """, (similarity_threshold, limit))

            similarities = cur.fetchall()

        # Create RELATED_TO edges in Neo4j
        with self.neo4j_driver.session() as session:
            for m1_id, m2_id, similarity in similarities:
                session.run("""
                    MATCH (m1:Memory {id: $m1_id})
                    MATCH (m2:Memory {id: $m2_id})
                    MERGE (m1)-[r:RELATED_TO]->(m2)
                    SET r.similarity = $similarity
                """, {"m1_id": str(m1_id), "m2_id": str(m2_id), "similarity": float(similarity)})

                self.stats["relationships_created"] += 1

        print(f"Created {len(similarities)} similarity edges.\n")

    def print_stats(self):
        """Print final statistics"""
        print("=" * 60)
        print("ETL PIPELINE COMPLETE")
        print("=" * 60)
        print(f"Memories processed:     {self.stats['memories_processed']:,}")
        print(f"Nodes created:          {self.stats['nodes_created']:,}")
        print(f"Relationships created:  {self.stats['relationships_created']:,}")
        print(f"Errors:                 {self.stats['errors']:,}")
        print("=" * 60)

    def run_full_pipeline(self, similarity_threshold=0.7):
        """Run complete ETL pipeline"""
        try:
            self.connect()
            self.setup_neo4j_schema()
            self.process_memories()
            self.build_similarity_edges(similarity_threshold=similarity_threshold)
            self.print_stats()
        finally:
            self.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='PostgreSQL to Neo4j ETL Pipeline')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing')
    parser.add_argument('--similarity', type=float, default=0.7, help='Similarity threshold for RELATED_TO edges')
    parser.add_argument('--skip-similarity', action='store_true', help='Skip similarity edge creation')

    args = parser.parse_args()

    builder = MemoryGraphBuilder()

    try:
        builder.connect()
        builder.setup_neo4j_schema()
        builder.process_memories(batch_size=args.batch_size)

        if not args.skip_similarity:
            builder.build_similarity_edges(similarity_threshold=args.similarity)

        builder.print_stats()
    finally:
        builder.close()
