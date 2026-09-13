import os
import logging
import httpx

from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp.mcp_client import MCPClient


logger = logging.getLogger(__name__)

# ExaAI provides information about code through web searches, crawling and code
# context searches through their platform. Requires no authentication.
EXAMPLE_MCP_ENDPOINT = "https://mcp.exa.ai/mcp"

def get_streamable_http_mcp_client() -> MCPClient:
    """Returns an MCP Client for Exa AI web search"""
    return MCPClient(lambda: streamable_http_client(EXAMPLE_MCP_ENDPOINT))


# Class needed to send updated AccessToken for each request to the Gateway
# Access Token renews after 60 minutes so we need to send it to Gateway for each request.
class DynamicBearerAuth(httpx.Auth):
    """Use the latest Cognito Authorization header for each Gateway request."""

    def __init__(self):
        self._auth_header: str | None = None

    def set_auth_header(self, auth_header: str) -> None:
        self._auth_header = auth_header

    def auth_flow(self, request):
        if self._auth_header:
            request.headers["Authorization"] = self._auth_header

        yield request

def get_gateway_mcp_client(dynamic_auth: DynamicBearerAuth) -> MCPClient | None:
    """Returns an MCP Client for AgentCore Gateway, if configured."""

    url = os.environ.get("AGENTCORE_GATEWAY_MY_GATEWAY_SECURE_URL")

    if not url:
        logger.warning("Gateway URL not set — gateway tools unavailable")
        return None

    # MCP 1.24 accepts a supplied httpx.AsyncClient. HTTPX evaluates the
    # DynamicBearerAuth auth flow for each outbound request, so a Cognito
    # access-token refresh does not require rebuilding the Agent.
    http_client = httpx.AsyncClient(auth=dynamic_auth)

    return MCPClient(
        lambda: streamable_http_client(
            url=url,
            http_client=http_client
        )
    )
