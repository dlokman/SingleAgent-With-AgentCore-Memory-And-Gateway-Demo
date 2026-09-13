import boto3
import json

# =========================
#  Using Amazon Bedrock AgentCore Data Plane
#  https://docs.aws.amazon.com/bedrock-agentcore/latest/APIReference/Welcome.html
#  boto3.client("bedrock-agentcore")   <=== This is the raw AWS service client for the AgentCore Data Plane APIs.
# =========================

REGION_NAME = "us-east-1"
MEMORY_ID = "FlightBookingSupport_SharedMemory-WxeZAr4460" # update with your MEMORY_ID from the environment variable after deployment
ACTOR_ID = "d4e83478-c0b1-70a0-7c9f-7d51c1782b98"
SESSION_ID = "8642cd54-8ce8-468c-85a6-e4ad5b85e336"  #update with your session id to see the relevant memories

# =========================
# CLIENT
# =========================

data_client = boto3.client("bedrock-agentcore", region_name=REGION_NAME)

# =========================================================
# SHORT-TERM MEMORY EVENTS
# =========================================================

all_events = []

try:

    print("\n" + "=" * 80)
    print("SHORT-TERM MEMORY EVENTS")
    print("=" * 80)

    next_token = None

    while True:

        request = {
            "memoryId": MEMORY_ID,
            "actorId": ACTOR_ID,
            "sessionId": SESSION_ID,
            "maxResults": 100
        }

        if next_token:
            request["nextToken"] = next_token

        response = data_client.list_events(**request) # list short term memory events

        events = response.get("events", [])

        all_events.extend(events)

        next_token = response.get("nextToken")

        if not next_token:
            break

    for idx, event in enumerate(all_events, start=1):
        print(f"\nEVENT #{idx}")
        print("-" * 80)
        print(json.dumps(event, indent=2, default=str))

except Exception as e:
    print(f"No short-term memory events found. {e}")

# =========================================================
# SHORT-TERM MEMORY CONVERSATION EVENTS
# =========================================================

print()
print()

# print("\n" + "=" * 80)
# print("SHORT-TERM MEMORY - CONVERSATION EVENTS")
# print("=" * 80)

# conversation_events = []

# for event in all_events:

#     payload = event.get("payload", [])

#     # payload is a LIST
#     if isinstance(payload, list):
#         conversation_events.extend(payload)

# for idx, message in enumerate(conversation_events, start=1):

#     role = message.get("role")

#     content = ""

#     if "content" in message:
#         content_obj = message["content"]

#         if isinstance(content_obj, dict):
#             content = content_obj.get("text", "")

#     print(f"Message {idx}")
#     print(f"  {role}: {content}")
#     print()

# =========================================================
# HELPER FUNCTION
# LIST MEMORY RECORDS
# =========================================================

def list_all_memory_records(namespace, max_results=100):

    next_token = None

    all_records = []

    try:
        while True:

            request = {
                "memoryId": MEMORY_ID,
                "namespace": namespace,
                "maxResults": max_results
            }

            if next_token:
                request["nextToken"] = next_token

            response = data_client.list_memory_records(**request)

            records = response.get("memoryRecordSummaries", [])

            all_records.extend(records)

            next_token = response.get("nextToken")

            if not next_token:
                break

        return all_records

    except Exception as e:
        print(f"No long-term memory events found. {e}")
        return all_records
# =========================================================
# HELPER FUNCTION
# RETRIEVE MEMORY RECORDS (SEMANTIC SEARCH)
# =========================================================

def retrieve_all_memory_records(namespace, query, max_results=100):

    next_token = None

    all_records = []

    try:

        while True:

            request = {
                "memoryId": MEMORY_ID,
                "namespace": namespace,
                "searchCriteria": {
                    "searchQuery": query   # has filter query
                },
                "maxResults": max_results
            }

            if next_token:
                request["nextToken"] = next_token

            response = data_client.retrieve_memory_records(**request)

            records = response.get("memoryRecordSummaries", [])

            all_records.extend(records)

            next_token = response.get("nextToken")

            if not next_token:
                break

        return all_records

    except Exception as e:
        print(f"No long-term memory events found. {e}")
        return all_records
# =========================================================
# LONG-TERM MEMORY — SEMANTIC
# Namespace:
# /users/{actorId}/facts
# =========================================================

semantic_namespace = f"/users/{ACTOR_ID}/facts"

print()
print("\n" + "=" * 80)
print("LONG-TERM MEMORY — SEMANTIC")
print("=" * 80)

semantic_memories = list_all_memory_records(
    namespace=semantic_namespace
)

for idx, memory in enumerate(semantic_memories, start=1):
    print(f"\nSEMANTIC MEMORY #{idx}")
    print("-" * 80)
    print(json.dumps(memory, indent=2, default=str))

# =========================================================
# CHECKING SCORE FOR SEMANTIC QUERY
# =========================================================

retrieved = retrieve_all_memory_records(
    namespace=semantic_namespace,
    query="What did I buy recently?"
)

print()
print("\n" + "=" * 80)
print("CHECKING SCORE FOR SEMANTIC QUERY:")
print("=" * 80)

print(json.dumps(retrieved, indent=2, default=str))


# =========================================================
# LONG-TERM MEMORY — SUMMARIZATION
# Namespace:
# /summaries/{actorId}/{sessionId}
# =========================================================

summary_namespace = f"/summaries/{ACTOR_ID}/{SESSION_ID}"

print("\n" + "=" * 80)
print("LONG-TERM MEMORY — SUMMARIZATION")
print("=" * 80)

summary_memories = list_all_memory_records(
    namespace=summary_namespace
)

for idx, memory in enumerate(summary_memories, start=1):
    print(f"\nSUMMARY MEMORY #{idx}")
    print("-" * 80)
    print(json.dumps(memory, indent=2, default=str))

# =========================================================
# LONG-TERM MEMORY — USER PREFERENCES
# Namespace:
# /users/{actorId}/preferences
# =========================================================

preferences_namespace = f"/users/{ACTOR_ID}/preferences"

print("\n" + "=" * 80)
print("LONG-TERM MEMORY — USER PREFERENCES")
print("=" * 80)

preferences_memories = list_all_memory_records(
    namespace=preferences_namespace
)

for idx, memory in enumerate(preferences_memories, start=1):
    print(f"\nUSER PREFERENCE MEMORY #{idx}")
    print("-" * 80)
    print(json.dumps(memory, indent=2, default=str))

# =========================================================
# LONG-TERM MEMORY — EPISODIC EXTRACTED MEMORIES
# Namespace:
# /episodes/{actorId}/{sessionId}
# =========================================================

episodic_extracted_namespace = f"/episodes/{ACTOR_ID}/{SESSION_ID}"

print("\n" + "=" * 80)
print("LONG-TERM MEMORY — EPISODIC EXTRACTED MEMORIES")
print("=" * 80)

episodic_extracted_memories = list_all_memory_records(
    namespace=episodic_extracted_namespace
)

for idx, memory in enumerate(episodic_extracted_memories, start=1):
    print(f"\nEPISODIC EXTRACTED MEMORY #{idx}")
    print("-" * 80)
    print(json.dumps(memory, indent=2, default=str))

# =========================================================
# LONG-TERM MEMORY — EPISODIC REFLECTION MEMORIES
# Namespace:
# /episodes/{actorId}
# =========================================================

episodic_reflection_namespace = f"/episodes/{ACTOR_ID}"

print("\n" + "=" * 80)
print("LONG-TERM MEMORY — EPISODIC REFLECTION MEMORIES")
print("=" * 80)

episodic_reflection_memories = list_all_memory_records(
    namespace=episodic_reflection_namespace
)

for idx, memory in enumerate(episodic_reflection_memories, start=1):
    print(f"\nEPISODIC REFLECTION MEMORY #{idx}")
    print("-" * 80)
    print(json.dumps(memory, indent=2, default=str))


# =========================================================
# CHECKING SCORE FOR Query - EpiSodic EXTRACTED MEMORY
# =========================================================

# retrieved = retrieve_all_memory_records(
#     namespace=episodic_extracted_namespace,
#     query="Book me a flight from Boston to Houston on June 16, 2026"
# )

# print()
# print("\n" + "=" * 80)
# print("CHECKING SCORE FOR  Query - Episodic EXTRACTED MEMORY")
# print("=" * 80)

# print(json.dumps(retrieved, indent=2, default=str))


# =========================================================
# CHECKING SCORE FOR Query - EpiSodic REFLECTION MEMORY
# =========================================================

# retrieved = retrieve_all_memory_records(
#     namespace=episodic_reflection_namespace,
#     query="Book me a flight from Boston to Houston on June 16, 2026"
# )

# print()
# print("\n" + "=" * 80)
# print("CHECKING SCORE FOR  Query - EpiSodic REFLECTION MEMORY")
# print("=" * 80)

# print(json.dumps(retrieved, indent=2, default=str))