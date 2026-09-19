# 🤖 Single Agent Chatbot with AgentCore Memory & Gateway

## 🧰 Tech Stack
- **Architecture:** AWS-Native Tech Stack
- **Project Setup:** UV-based project created using the AgentCore CLI
- **Hosting Platform:** Amazon Bedrock AgentCore
- **AI Agent Framework:** Strands Agents SDK
- **MCP Server:** AgentCore Gateway → AWS Lambda Target
- **Programming Language:** Python

<a id="architecture-diagram"></a>
## 🏗️ Architecture Overview
![architecture](Architecture-Diagram.svg)

## 🌟 Project Overview

### Models

- **Foundation Model:** Claude Sonnet 4.6


### Summary

- This is a FlightBookingSupport Demo using Single Agent Chatbot with AgentCore Memory & Gateway

## 🗺️ Implementation Overview

### Authentication

Authentication between **Angular** and **AgentCoreRuntime** and **AgentCoreGateway** is done using JWT token from **AWS Cognito**

AgentCoreGateway code includes provision for new access token after 60 minutes expiry

### Local Tools
- get_all_fare_classes
- search_flights
- get_all_bookings_for_passenger
- create_booking
- cancel_booking

### Agentcore Gateway Target
 - get_fare_policy Lambda Function

### AgentCore Memory Types

1. **Short Term Memory(Conversation history)**
   - 7 days Expiration

2. **Long Term Memory**
   - SEMANTIC
   - SUMMARIZATION
   - USER_PREFERENCE
   - Episodic Extracted Memories
   - Episodic Reflection Memories

**Command to Add Memory**: agentcore add memory --name SharedMemory  --strategies "SEMANTIC,SUMMARIZATION,USER_PREFERENCE,EPISODIC" --expiry 7

### Other Features

- Includes Cloudformation Stack for provisioning resources

- Includes AgentCore Evaluations

- Admin User gate access to application by creating users via script and assigning user to a group for role based access

- Includes extracting memory records using a script for troubleshooting


## 📁 Folder Hierarchy

```
FlightBookingSupport/
│
├── agentcore/
│
├── app/
│   └── FlightBookingAgent/
│       ├── __pycache__/
│       ├── .venv/
│       ├── mcp_client/
│       ├── memory/
│       ├── model/
│       ├── skills/
│       ├── tool/
│       ├── .gitignore
│       ├── dump-all-memories-using-aws-sdk.py    # dump all memories for debugging purposes
│       ├── main.py
│       ├── pyproject.toml
│       ├── README.md
│       └── uv.lock
│
├── infrastructure/
│   ├── cloud-formation-stack.yml                  # cloudformation stack to provision resources
│   └── Create-User-Commands.txt                   # contains admin scripts to create users and gate access to application
│
├── AGENTS.md
└── README.md

```

## ⚙️ Project Installation (After Cloning the Repository)

1. From the `FlightBookingSupport/agentcore/cdk` folder (CDK is an npm-based project), run:

   ```powershell
   npm ci (installs exactly from the package-lock.json)
   ```

2. From the `FlightBookingSupport/app/FlightBookingAgent` folder (same level as `pyproject.toml`), run:

   ```powershell
   uv sync    (creates .venv virtual environment as well)
   ```
<br>

## 🧪 Testcases

```text

**AgentCore Memory Test**
Login with dan.lokman@hotmail.com to FlightBookingAgent
Hi, What can you do?
My name is Dan and I prefer window seats.         <====== Stored in User Preferences (Long Term Memory). Can be retrieved cross sessions
Logout and Log back In Or Click on New Chat       <====== Will use a New Session ID. Wait 1-2 minutes for Long Term Memory to be generated
What do i prefer?                                 <====== Information Retrieved from Semantic- Long Term Memory

In another browser login with dlokman746@gmail.com to FlightBookingAgent
What do i prefer?                                 <====== No Memories Or Old memories. Memory is specific for user

I just bought a Mechanical Keyboard               <====== Stored in Semantic Memory (Long Term Memory). Can be retrieved cross sessions
Logout and Log back In - Or  Click on New Chat    <====== Will use a New Session ID. Wait 1-2 minutes for Long Term Memory to be generated
What did i just buy?                              <====== Information Retrieved from Semantic- Long Term Memory

I own a HP Elitebook Laptop                       <====== stored in Semantic Memory

**AgentCore Gateway Test**
Gateway Target is Lambda Function called workshop-get-fare-policy

List all available fare classes                       <====== Local tool invoked
What is the fare policy for economy_flex fare class?  <====== Model will invoke Gateway Target: Lambda Function workshop-get-fare-policy to get the result

**Local Tools Test**
Find me flights from Houston to Seattle on October 15, 2026.   <====== Search for flights
Book FLT-102 for John Smith
Show me all bookings for John Smith.                           <====== Retrieve Bookings
Cancel John Smith's FLT-102 booking                            <====== Before cancelling, model will call get_all_bookings_for_passenger(passenger_name) to verify passenger currently has the booking
Show me all bookings for John Smith                            <====== Verify deletion

**Error conditions test**
Find me flights from Houston to Los Angeles on October 15, 2026. <====== No Flights
Book FLT-999 for John Smith.                                     <====== Try to Book an Invalid flight ID
After John already has FLT-102: Book FLT-102 for John Smith.     <====== Duplicate booking
Cancel booking BK-DOESNOTEXIST for John Smith.                   <====== Cancel nonexistent booking

```
