from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from mcp_client.client import get_streamable_http_mcp_client, get_gateway_mcp_client, DynamicBearerAuth
import uuid
import logging
from memory.session import get_memory_session_manager
import jwt
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s"
)
log = logging.getLogger(__name__)

app = BedrockAgentCoreApp()


SYSTEM_PROMPT = """
You are an airline booking assistant.

You help users search for flights, view available fare classes, search fare policies, create bookings, and cancel bookings.

Follow these rules:

1. When a user asks for available fare classes, use get_all_fare_classes.
   When displaying fare classes returned by get_all_fare_classes, preserve the exact fare class values returned by the tool. Do not rename or format the values.

2. When a user wants to find a flight, use search_flights.

   search_flights requires:
   - origin
   - destination
   - departure_date

   Users may provide city names such as Houston and Seattle or airport codes such as HOU and SEA.

   Convert dates provided by the user into YYYY-MM-DD format when calling search_flights.

3. Never invent a flight ID.

   If the user wants to book a flight but has not provided a flight ID, ask the user to provide the flight ID.

   If the user provides a flight ID, proceed with the booking workflow.

4. Before creating any booking:
   - Always call get_all_bookings_for_passenger for that passenger.
   - Check whether the passenger already has a booking for the same flight.
   - If the same booking already exists, do not call create_booking.
   - Inform the user that the booking already exists.
   - Otherwise, call create_booking.

5. Before cancelling any booking:
   - Always call get_all_bookings_for_passenger for that passenger.
   - Verify that the passenger currently has the requested booking.
   - If the booking does not exist, do not call cancel_booking.
   - Inform the user that no matching booking was found.
   - If the booking exists, use its booking ID to call cancel_booking.

6. Call get_fare_policy when the user asks about fare policy for a specific fare class.

7. Never invent flight IDs, booking IDs, prices, fare classes, passenger names, booking information, or fare policies.
   Use information provided by the user or returned by tools.

8. Never create duplicate bookings for the same passenger and flight.

9. If a tool returns an error or indicates that something was not found, explain that result to the user instead of claiming that the action succeeded.

"""


# --- FlightBookingAgent Tools ---

AIRPORT_CODES = {
    "houston": "HOU",
    "seattle": "SEA",
    "new york": "NYC",
    "hou": "HOU",
    "sea": "SEA",
    "nyc": "NYC"
}

FLIGHTS = {
    "FLT-101": {
        "airline": "SkyWay Airlines",
        "origin": "HOU",
        "destination": "SEA",
        "departure": "2026-10-15 08:00",
        "price": 289.99,
        "fare_class": "economy"
    },
    "FLT-102": {
        "airline": "SkyWay Airlines",
        "origin": "HOU",
        "destination": "SEA",
        "departure": "2026-10-15 13:30",
        "price": 349.99,
        "fare_class": "economy_flex"
    },
    "FLT-103": {
        "airline": "CloudJet",
        "origin": "HOU",
        "destination": "NYC",
        "departure": "2026-10-20 09:00",
        "price": 319.99,
        "fare_class": "economy"
    }
}

# Normally this would be in a database
BOOKINGS = {}

@tool
def get_all_fare_classes() -> list[str]:
    """Get all available fare classes.

    Returns:
        List of available fare classes.
    """

    return ["economy", "economy_flex", "business"]


@tool
def search_flights(origin: str, destination: str, departure_date: str) -> str:
    """Search for available flights.

    The origin and destination can be city names or airport codes.

    The departure date should be provided in YYYY-MM-DD format.

    Examples:
        Houston, Seattle, 2026-10-15
        HOU, SEA, 2026-10-15

    Args:
        origin: Departure city or airport code
        destination: Destination city or airport code
        departure_date: Departure date in YYYY-MM-DD format

    Returns:
        Matching available flights
    """

    origin_key = origin.strip().lower()
    destination_key = destination.strip().lower()
    departure_date = departure_date.strip()

    origin_code = AIRPORT_CODES.get(origin_key, origin.upper())
    destination_code = AIRPORT_CODES.get(destination_key, destination.upper())

    results = []

    for flight_id, flight in FLIGHTS.items():
        flight_date = flight["departure"].split(" ")[0]

        if (flight["origin"] == origin_code and flight["destination"] == destination_code and flight_date == departure_date):
            results.append(
                f"{flight_id}: "
                f"{flight['airline']}, "
                f"{flight['departure']}, "
                f"${flight['price']}, "
                f"{flight['fare_class']}"
            )

    if results:
        return "Available flights:\n" + "\n".join(results)

    return (
        f"No flights found from {origin} to {destination} "
        f"on {departure_date}"
    )


@tool
def get_all_bookings_for_passenger(passenger_name: str) -> str:
    """Get all current bookings for a passenger.

    Args:
        passenger_name: Name of the passenger

    Returns:
        All current bookings for the passenger
    """

    results = []

    for booking_id, booking in BOOKINGS.items():
        if booking["passenger_name"].lower() == passenger_name.lower():
            results.append(
                f"{booking_id}: "
                f"Flight: {booking['flight_id']}, "
                f"Amount: ${booking['amount']}, "
                f"Fare class: {booking['fare_class']}"
            )

    if results:
        return (
            f"Bookings for {passenger_name}:\n"
            + "\n".join(results)
        )

    return f"No bookings found for {passenger_name}"


@tool
def create_booking(flight_id: str, passenger_name: str) -> str:
    """Create a booking for a passenger.

    Before calling this tool, always use get_all_bookings_for_passenger(passenger_name) to check whether the passenger already has a booking for the same flight.

    If the passenger already has the same flight booking, do not call this tool. Inform the user that the booking already exists.

    Args:
        flight_id: Flight ID such as FLT-101
        passenger_name: Name of the passenger

    Returns:
        Created booking details
    """

    flight_id = flight_id.upper()

    if flight_id not in FLIGHTS:
        return f"Flight {flight_id} not found"

    # Defensive duplicate check
    for booking in BOOKINGS.values():
        if (booking["passenger_name"].lower() == passenger_name.lower() and booking["flight_id"] == flight_id):
            return (
                f"{passenger_name} already has a booking "
                f"for flight {flight_id}"
            )

    flight = FLIGHTS[flight_id]

    booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"

    BOOKINGS[booking_id] = {
        "passenger_name": passenger_name,
        "flight_id": flight_id,
        "amount": flight["price"],
        "fare_class": flight["fare_class"]
    }

    return (
        f"Booking created successfully. "
        f"Booking ID: {booking_id}, "
        f"Passenger: {passenger_name}, "
        f"Flight: {flight_id}, "
        f"Amount: ${flight['price']}"
    )


@tool
def cancel_booking(booking_id: str, passenger_name: str) -> str:
    """Cancel an existing booking.

    Before calling this tool, always use get_all_bookings_for_passenger(passenger_name) to verify that the passenger currently has the booking they are trying
    to cancel.

    If the booking does not exist for that passenger, do not call this tool. Inform the user that no matching booking was found.

    Args:
        booking_id: Booking ID such as BK-7A91C3F2
        passenger_name: Name of the passenger

    Returns:
        Cancelled booking details
    """

    booking_id = booking_id.upper()

    if booking_id not in BOOKINGS:
        return f"Booking {booking_id} not found"

    booking = BOOKINGS[booking_id]

    if booking["passenger_name"].lower() != passenger_name.lower():
        return (
            f"Booking {booking_id} does not belong to "
            f"{passenger_name}"
        )

    cancelled_booking = BOOKINGS.pop(booking_id)

    return (
        f"Booking {booking_id} cancelled successfully. "
        f"Passenger: {cancelled_booking['passenger_name']}, "
        f"Flight: {cancelled_booking['flight_id']}, "
        f"Amount: ${cancelled_booking['amount']}, "
        f"Fare class: {cancelled_booking['fare_class']}"
    )


# --- Agent Setup ---

_agent = None

# This object is shared with the Gateway MCP HTTP client.
# Its Authorization header is refreshed on every AgentCore Runtime invocation.
_gateway_auth = DynamicBearerAuth()

def get_or_create_agent(session_id, user_id, auth_header):
    global _agent

	# Access Token renews after 60 minutes so we need to send it to Gateway for each request.
    _gateway_auth.set_auth_header(auth_header)

    if _agent is None:
        session_manager = get_memory_session_manager(session_id, user_id)  # will persist raw conversation as Short Term Memory in AgentCore Memory. We configured this to 7 days in agentcore.json

        # Create MCP clients only when the Agent is first created.
        mcp_clients = [get_streamable_http_mcp_client(), get_gateway_mcp_client(_gateway_auth)]

        tools = [get_all_fare_classes, search_flights, get_all_bookings_for_passenger, create_booking, cancel_booking]

        for mcp_client in mcp_clients:
            if mcp_client:
                tools.append(mcp_client)

        _agent = Agent(
            model=load_model(),
            session_manager=session_manager,
            system_prompt=SYSTEM_PROMPT,
            tools=tools
        )

    return _agent

def extract_user_id(auth_header) -> str | None:
    """Extract user_id from JWT bearer token (username claim) or fall back to custom header."""

    if auth_header and auth_header.startswith("Bearer "):
        try:
            # Format: Bearer eyJhbGciOiJSUzI1NiIs...
            token = auth_header.split(" ", 1)[1]  # Gets the JWT token part after "Bearer "
            claims = jwt.decode(token, options={"verify_signature": False})
             #For Debugging. Log JWT Claims
            # log.info("JWT claims: %s", json.dumps(claims, indent=2))
            # groups = claims.get("cognito:groups", [])   # tells you which groups this user belongs to e.g ["Admins", "FlightAgents"]
            username = claims.get("username")
            if username:
                return username
        except Exception as e:
            log.warning(f"Failed to decode JWT for user_id: {e}")
    else:
        log.info(f"No Bearer token found. Auth header present: {auth_header is not None}")
        raise Exception("No Authorization header")


@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Agent.....")

    session_id = context.session_id
    request_headers = context.request_headers

    # Access request headers - handle None case
    request_headers = context.request_headers or {}

    # Get Client JWT token
    auth_header = request_headers.get('Authorization', '')

    if not auth_header:
        raise Exception("No authorization header")

    user_id = extract_user_id(auth_header)

    if not session_id or not user_id:
        raise ValueError("session_id and user_id are required. Pass --session-id and --user-id when invoking.")

    agent = get_or_create_agent(session_id, user_id, auth_header)

    # Stream Strands events back through AgentCore
    async for event in agent.stream_async(payload.get("prompt")):

        if not isinstance(event, dict) or "event" not in event:
            continue

        cbs = event["event"].get("contentBlockStart")

        if cbs is not None and not cbs.get("start"):
            continue

        yield event


if __name__ == "__main__":
    app.run()




