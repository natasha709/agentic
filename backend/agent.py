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

# --- Tools Definition ---

@tool
def get_server_metrics(server_id: str):
    """Get CPU, RAM, and Disk metrics for a specific server."""
    # Mock data for assignment
    return {
        "server_id": server_id,
        "cpu_usage": "85%",
        "ram_usage": "92%",
        "disk_usage": "98%",
        "status": "Warning"
    }

@tool
def search_runbooks(query: str):
    """Search the official IT runbooks for troubleshooting instructions."""
    # Simulating RAG response
    if "vpn" in query.lower():
        return "VPN SOP: Ensure credentials are correct, check connection, restart client."
    elif "slow" in query.lower() or "website" in query.lower():
        return "Slow Website SOP: Check server metrics, clear caches, check error logs."
    return "No specific runbook found. Escalate to senior IT staff."

@tool
def restart_service(service_name: str):
    """Restart a backend service. Requires confirmation."""
    return f"Service '{service_name}' has been successfully restarted."

tools = [get_server_metrics, search_runbooks, restart_service]
tool_node = ToolNode(tools)

# --- Graph Design ---

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The list of messages in the conversation"]
    next_step: str

# Define the node that decides what to do
def call_model(state: AgentState):
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
    llm_with_tools = llm.bind_tools(tools)
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
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
