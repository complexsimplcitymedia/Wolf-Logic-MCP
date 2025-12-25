#!/bin/bash
# Start Neo4j
docker start neo4j 2>/dev/null || docker run -d --name neo4j -p 7474:7474 -p 7687:7687 neo4j
echo "Neo4j started"
