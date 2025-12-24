import os
from mem0 import Memory

os.environ["OLLAMA_BASE_URL"] = "https://ollama.complexsimplicityai.com"

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "openmemory",
            "host": "localhost",
            "port": 6333,
        }
    }
}

m = Memory.from_config(config)
messages = [
    {"role": "user", "content": "I'm planning to watch a movie tonight. Any recommendations?"},
    {"role": "assistant", "content": "How about thriller movies? They can be quite engaging."},
    {"role": "user", "content": "I’m not a big fan of thriller movies but I love sci-fi movies."},
    {"role": "assistant", "content": "Got it! I'll avoid thriller recommendations and suggest sci-fi movies in the future."}
]
m.add(messages, user_id="alice", metadata={"category": "movies"})