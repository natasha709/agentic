import os
from typing import Annotated, List, TypedDict, Union
from typing_extensions import Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

# --- Reasoning Logs ---
reasoning_logs = []

def add_reasoning_log(label: str, message: str, status: str = "processing"):
    """Add a reasoning log entry."""
    reasoning_logs.append({
        "label": label,
        "message": message,
        "status": status
    })

def get_reasoning_logs():
    """Get all reasoning logs and clear the list."""
    global reasoning_logs
    logs = reasoning_logs.copy()
    reasoning_logs = []
    return logs

def clear_reasoning_logs():
    """Clear all reasoning logs."""
    global reasoning_logs
    reasoning_logs = []

# --- Tools Definition ---

@tool
def get_server_metrics(server_id: str):
    """Get CPU, RAM, and Disk metrics for a specific server."""
    add_reasoning_log("TOOL", f"Executing get_server_metrics for server: {server_id}", "processing")
    # Mock data for assignment
    result = {
        "server_id": server_id,
        "cpu_usage": "85%",
        "ram_usage": "92%",
        "disk_usage": "98%",
        "status": "Warning"
    }
    add_reasoning_log("TOOL", f"get_server_metrics returned: {result}", "success")
    return result

@tool
def search_runbooks(query: str):
    """Search the official IT runbooks for troubleshooting instructions."""
    add_reasoning_log("TOOL", f"Searching runbooks for: {query}", "processing")
    # Simulating RAG response
    if "vpn" in query.lower():
        result = "VPN SOP: Ensure credentials are correct, check connection, restart client."
    elif "slow" in query.lower() or "website" in query.lower():
        result = "Slow Website SOP: Check server metrics, clear caches, check error logs."
    else:
        result = "No specific runbook found. Escalate to senior IT staff."
    add_reasoning_log("TOOL", f"search_runbooks returned: {result}", "success")
    return result

@tool
def restart_service(service_name: str):
    """Restart a backend service. Requires confirmation."""
    add_reasoning_log("TOOL", f"Executing restart_service for: {service_name}", "processing")
    result = f"Service '{service_name}' has been successfully restarted."
    add_reasoning_log("TOOL", f"restart_service returned: {result}", "success")
    return result

tools = [get_server_metrics, search_runbooks, restart_service]
tool_node = ToolNode(tools)

# --- Graph Design ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The list of messages in the conversation"]
    next_step: str

# Define the node that decides what to do
def call_model(state: AgentState):
    add_reasoning_log("REASONING", "Invoking LLM with tools...", "processing")
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
    llm_with_tools = llm.bind_tools(tools)
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    
    # Log the LLM's decision
    if response.tool_calls:
        tool_names = [tc['name'] for tc in response.tool_calls]
        add_reasoning_log("REASONING", f"LLM decided to call tools: {tool_names}", "success")
    else:
        add_reasoning_log("REASONING", "LLM decided to respond directly (no tools needed)", "success")
    
    return {"messages": [response]}

def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

# Initialize Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()
