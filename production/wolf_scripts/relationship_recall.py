import os
from mem0 import Memory

config = {
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": os.environ["NEO4J_URL"],
            "username": os.environ["NEO4J_USERNAME"],
            "password": os.environ["NEO4J_PASSWORD"],
            "database": "neo4j",
        }
    }
}

memory = Memory.from_config(config)

conversation = [
    {"role": "user", "content": "Alice met Bob at GraphConf 2025 in San Francisco."},
    {"role": "assistant", "content": "Great! Logging that connection."},
]

memory.add(conversation, user_id="demo-user")

results = memory.search(
    "Who did Alice meet at GraphConf?",
    user_id="demo-user",
    limit=3,
    rerank=True,
)

for hit in results["results"]:
    print(hit["memory"])
