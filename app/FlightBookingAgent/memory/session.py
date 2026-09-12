import os
from typing import Optional
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# The memory ID is injected as an environment variable (MEMORY_SHAREDMEMORY_ID) by the AgentCore Runtime after deployment
# SHAREDMEMORY is the name we gave to the memory when we added it via AgentCore CLI
# SHAREDMEMORY Has to be ALl Uppercase. Even if in agentcore.json has it named as SharedMemory
MEMORY_ID = os.getenv("MEMORY_SHAREDMEMORY_ID")

# AgentCore CLI injects due to settings in aws-targets.json
REGION = os.getenv("AWS_REGION")

print(f"Memory Configuration - MEMORY_ID: {MEMORY_ID}, REGION: {REGION}")

def get_memory_session_manager(session_id: str, actor_id: str) -> Optional[AgentCoreMemorySessionManager]:
    if not MEMORY_ID:
        return None

    retrieval_config = {
        f"/users/{actor_id}/facts": RetrievalConfig(top_k=3, relevance_score=0.2),            # SEMANTIC
        f"/summaries/{actor_id}/{session_id}": RetrievalConfig(top_k=3, relevance_score=0.2), # SUMMARIZATION
        f"/users/{actor_id}/preferences": RetrievalConfig(top_k=3, relevance_score=0.2),      # USER_PREFERENCE
        f"/episodes/{actor_id}/{session_id}": RetrievalConfig(top_k=3, relevance_score=0.2),  # Episodic Extracted Memories. Could take anywhere between 1-20 minutes to generate
        f"/episodes/{actor_id}": RetrievalConfig(top_k=3, relevance_score=0.2)                # Episodic Reflection Memories. Could take anywhere between 1-20 minutes to generate
    }

# USER_PREFERENCE: /users/{actorId}/preferences
# EPISODIC:        /episodes/{actorId}/{sessionId}
#                  /episodes/{actorId}

    return AgentCoreMemorySessionManager(
        AgentCoreMemoryConfig(
            memory_id=MEMORY_ID,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config=retrieval_config,
        ),
        REGION
    )