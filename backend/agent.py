"""
Sentinel AI - Agentic IT Support Assistant
Complete Implementation for Agentic AI Internship Assignment

Architecture:
- Thought → Action → Observation → Reflection loop
- RAG-powered knowledge retrieval
- Memory persistence across sessions
- Safety controls with prompt injection detection
- Comprehensive observability
"""

import os
import json
import hashlib
import re
from datetime import datetime
from typing import Annotated, List, TypedDict, Dict, Any, Optional
from typing_extensions import Literal
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from dotenv import load_dotenv

# Load .env from the backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)


class ObservabilityLogger:
    """Comprehensive observability system for agent reasoning"""
    
    def __init__(self):
        self.logs = []
        self.session_id = None
        
    def set_session(self, session_id: str):
        self.session_id = session_id
        self.logs = []
        
    def add_log(self, category: str, message: str, status: str = "processing", 
                metadata: Dict[str, Any] = None):
        """Add a structured log entry"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,  
            "message": message,
            "status": status,  
            "metadata": metadata or {}
        }
        self.logs.append(entry)
        
    def add_thought(self, thought: str, reasoning: str = None):
        """Log agent thought process"""
        self.add_log("THOUGHT", thought, metadata={"reasoning": reasoning})
        
    def add_action(self, action: str, tool_name: str, inputs: Dict[str, Any]):
        """Log tool action being taken"""
        self.add_log("ACTION", f"Executing {action}", metadata={
            "tool": tool_name,
            "inputs": inputs
        })
        
    def add_observation(self, observation: str, outputs: Any = None):
        """Log observation from tool result"""
        self.add_log("OBSERVATION", observation, metadata={"outputs": str(outputs)[:500] if outputs else None})
        
    def add_reflection(self, reflection: str, next_step: str = None):
        """Log reflection on the result"""
        self.add_log("REFLECTION", reflection, metadata={"next_step": next_step})
        
    def add_safety(self, event: str, details: str, passed: bool = True):
        """Log safety event"""
        self.add_log("SAFETY", f"{event}: {details}", status="success" if passed else "error")
        
    def add_error(self, error: str, recovery_action: str = None):
        """Log error and potential recovery"""
        self.add_log("ERROR", error, status="error", metadata={"recovery": recovery_action})
        
    def get_logs(self) -> List[Dict]:
        logs = self.logs.copy()
        return logs
    
    def clear(self):
        self.logs = []

# Global logger instance
logger = ObservabilityLogger()



class SafetyController:
    """Safety controls for prompt injection, tool misuse, and sensitive data"""
    
    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS = [
        r"ignore previous instructions",
        r"ignore all previous",
        r"disregard.*instructions",
        r"forget.*rules",
        r"new instructions:",
        r"override.*system",
        r"you are now",
        r"pretend to be",
        r"act as if",
        r"developer mode",
        r"jailbreak",
        r"dan mode",
        r"enable sudo"
    ]
    
    # Sensitive data patterns to redact
    SENSITIVE_PATTERNS = [
        r"\b\d{16}\b",  
        r"\b\d{3}-\d{2}-\d{4}\b",  
        r"api[_-]?key['\"]?\s*[:=]\s*['\"]?\w+",
        r"password['\"]?\s*[:=]\s*['\"]?\w+",
        r"secret['\"]?\s*[:=]\s*['\"]?\w+",
        r"token['\"]?\s*[:=]\s*['\"]?\w+"
    ]
    
    # Risky tools that require confirmation
    RISKY_TOOLS = ["restart_service", "create_ticket", "delete_data"]
    
    @classmethod
    def check_prompt_injection(cls, user_input: str) -> tuple[bool, str]:
        """Detect prompt injection attempts"""
        user_lower = user_input.lower()
        
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, user_lower):
                return True, f"Potential prompt injection detected: matched pattern '{pattern}'"
        
        return False, "No injection detected"
    
    @classmethod
    def redact_sensitive_data(cls, text: str) -> str:
        """Redact sensitive information from text"""
        redacted = text
        
        for pattern in cls.SENSITIVE_PATTERNS:
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)
        
        return redacted
    
    @classmethod
    def requires_confirmation(cls, tool_name: str) -> bool:
        """Check if tool requires user confirmation"""
        return tool_name in cls.RISKY_TOOLS
    
    @classmethod
    def validate_tool_usage(cls, tool_name: str, args: Dict) -> tuple[bool, str]:
        """Validate tool is being used appropriately"""
        # Check for suspicious argument patterns
        if tool_name == "restart_service":
            # Block restarting critical systems
            critical_systems = ["mainframe", "production-db", "root"]
            if any(s in str(args.get("service_name", "")).lower() for s in critical_systems):
                return False, f"Cannot restart critical system: {args.get('service_name')}"
                
        return True, "Tool usage validated"

safety = SafetyController()



class ConversationMemory:
    """Persistent memory for conversation context"""
    
    def __init__(self, max_turns: int = 10):
        self.sessions: Dict[str, List[Dict]] = {}
        self.max_turns = max_turns
        
    def get_session(self, thread_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        return self.sessions.get(thread_id, [])
    
    def add_turn(self, thread_id: str, user_message: str, agent_response: str, 
                 tools_used: List[str] = None):
        """Add a turn to conversation history"""
        if thread_id not in self.sessions:
            self.sessions[thread_id] = []
            
        turn = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "agent": agent_response,
            "tools": tools_used or []
        }
        
        self.sessions[thread_id].append(turn)
        
        # Trim to max turns
        if len(self.sessions[thread_id]) > self.max_turns:
            self.sessions[thread_id] = self.sessions[thread_id][-self.max_turns:]
            
    def get_context_summary(self, thread_id: str) -> str:
        """Get a summary of recent conversation context"""
        history = self.get_session(thread_id)
        
        if not history:
            return "No previous context."
            
        summary_parts = []
        for turn in history[-3:]:  
            summary_parts.append(f"User: {turn['user'][:100]}")
            summary_parts.append(f"Agent: {turn['agent'][:100]}")
            
        return "\n".join(summary_parts)
    
    def clear_session(self, thread_id: str):
        """Clear a specific session"""
        if thread_id in self.sessions:
            del self.sessions[thread_id]

# Global memory instance
memory = ConversationMemory()



class KnowledgeBaseRAG:
    """RAG system using ChromaDB for knowledge retrieval"""
    
    def __init__(self):
        self.initialized = False
        self.runbooks = {}
        
    def initialize(self):
        """Initialize the RAG system with runbook data"""
        if self.initialized:
            return
            
        # Load runbook documents
        self.runbooks = {
            "vpn_troubleshooting": {
                "title": "VPN Troubleshooting Guide",
                "content": """
                VPN Connection Issues - Standard Operating Procedure:
                
                1. Check Internet Connection
                   - Verify internet connectivity by visiting any website
                   - Try pinging 8.8.8.8 to test basic connectivity
                   
                2. Verify VPN Credentials
                   - Ensure username and password are correct
                   - Check if account is active and not expired
                   - Verify multi-factor authentication is working
                   
                3. Check VPN Client Status
                   - Verify VPN client is running
                   - Check if connected to correct VPN server
                   - Try disconnecting and reconnecting
                   
                4. Network Troubleshooting
                   - Check firewall settings (port 443, 1194)
                   - Verify no network policies blocking VPN
                   - Try different VPN protocol (OpenVPN, IKEv2, WireGuard)
                   
                5. Contact IT Support
                   - If issue persists, create ticket with network team
                """,
                "category": "network"
            },
            "website_performance": {
                "title": "Website Performance Issues",
                "content": """
                Website Performance Troubleshooting Guide:
                
                1. Check Server Metrics
                   - CPU usage should be below 80%
                   - RAM usage should be below 85%
                   - Disk I/O should be normal
                   
                2. Check Application Logs
                   - Review error logs for exceptions
                   - Check for database connection issues
                   - Look for timeout errors
                   
                3. Network Analysis
                   - Check CDN status and configuration
                   - Verify DNS resolution
                   - Test SSL certificate validity
                   
                4. Cache Management
                   - Clear browser cache
                   - Clear application cache
                   - Check cache server status
                   
                5. Database Performance
                   - Check query performance
                   - Look for long-running queries
                   - Verify database connections
                """,
                "category": "web"
            },
            "disk_space": {
                "title": "High Disk Usage Resolution",
                "content": """
                Disk Space Management Guide:
                
                1. Identify High Usage
                   - Run disk usage analysis
                   - Identify largest directories
                   - Check for log file accumulation
                   
                2. Common Solutions
                   - Clear old log files (find /var/log -type f -mtime +30)
                   - Remove temporary files
                   - Clean package manager cache
                   - Archive old data
                   
                3. Monitor Trends
                   - Set up disk usage alerts
                   - Review weekly usage reports
                   - Plan capacity upgrades if needed
                """,
                "category": "storage"
            },
            "service_restart": {
                "title": "Service Restart Procedures",
                "content": """
                Service Restart and Recovery Guide:
                
                1. Assessment Phase
                   - Check service status first
                   - Review recent logs for errors
                   - Identify root cause
                   
                2. Restart Procedure
                   - Graceful restart preferred over force stop
                   - Verify no active connections
                   - Use service-specific restart commands
                   
                3. Post-Restart
                   - Verify service is running
                   - Check application logs
                   - Monitor for stability
                   - Notify affected users
                   
                4. Escalation
                   - If service won't start, escalate immediately
                   - Check with senior engineers
                   - Prepare incident report
                """,
                "category": "infrastructure"
            },
            "email_sync": {
                "title": "Email Synchronization Issues",
                "content": """
                Email Sync Troubleshooting Guide:
                
                1. Check Account Status
                   - Verify account is active
                   - Check mailbox quota
                   - Verify correct email settings
                   
                2. Network and Authentication
                   - Verify internet connectivity
                   - Check SMTP/IMAP server status
                   - Re-authenticate if needed
                   
                3. Client Settings
                   - Verify incoming/outgoing server settings
                   - Check SSL/TLS configuration
                   - Try different email client
                   
                4. Server-Side
                   - Check mail queue status
                   - Verify no mailbox corruption
                   - Check with email admin
                """,
                "category": "email"
            }
        }
        self.initialized = True
        
    def search(self, query: str, category: str = None) -> List[Dict]:
        """Search the knowledge base"""
        self.initialize()
        
        results = []
        query_lower = query.lower()
        
        # Keyword matching
        keywords = {
            "vpn": "vpn_troubleshooting",
            "connection": "vpn_troubleshooting",
            "remote": "vpn_troubleshooting",
            "website": "website_performance",
            "slow": "website_performance",
            "performance": "website_performance",
            "disk": "disk_space",
            "storage": "disk_space",
            "service": "service_restart",
            "restart": "service_restart",
            "email": "email_sync",
            "mail": "email_sync"
        }
        
        # Find relevant runbooks
        matched_keys = []
        for keyword, runbook_key in keywords.items():
            if keyword in query_lower:
                matched_keys.append(runbook_key)
        
        # If no keyword matches, return all
        if not matched_keys:
            matched_keys = list(self.runbooks.keys())
            
        for key in matched_keys:
            if key in self.runbooks:
                rb = self.runbooks[key]
                if category is None or rb["category"] == category:
                    results.append({
                        "title": rb["title"],
                        "content": rb["content"].strip(),
                        "category": rb["category"],
                        "relevance": 1.0 if key in matched_keys else 0.5
                    })
                    
        return results

# Global RAG instance
rag = KnowledgeBaseRAG()



@tool
def kb_search(query: str, category: str = None):
    """
    Search the IT Knowledge Base for troubleshooting guides and runbooks.
    Use this to find relevant documentation for IT issues.
    
    Args:
        query: The search query describing the issue
        category: Optional category filter (network, web, storage, infrastructure, email)
    
    Returns:
        List of relevant runbook articles with troubleshooting steps
    """
    logger.add_action("Search Knowledge Base", "kb_search", {"query": query, "category": category})
    
    results = rag.search(query, category)
    
    if results:
        response = f"Found {len(results)} relevant runbook(s):\n\n"
        for i, r in enumerate(results, 1):
            response += f"--- Runbook {i}: {r['title']} ({r['category']}) ---\n{r['content']}\n\n"
    else:
        response = "No relevant runbooks found. Please escalate to senior IT staff."
    
    logger.add_observation(f"Knowledge base returned {len(results)} results", results[:2])
    return response

@tool
def log_search(service: str, log_type: str = "error", lines: int = 50):
    """
    Search system logs for a specific service.
    
    Args:
        service: The service name to search logs for (e.g., 'nginx', 'database', 'vpn')
        log_type: Type of logs to search (error, warning, info, all)
        lines: Number of log lines to retrieve (default 50)
    
    Returns:
        Recent log entries for the specified service
    """
    logger.add_action("Search System Logs", "log_search", {"service": service, "log_type": log_type, "lines": lines})
    
    # Mock log data for demonstration
    mock_logs = {
        "nginx": {
            "error": [
                "[2026-03-02 10:23:45] ERROR: upstream connection timeout",
                "[2026-03-02 10:24:12] ERROR: 504 Gateway Timeout",
                "[2026-03-02 10:25:30] ERROR: worker process exited with code 1"
            ],
            "warning": [
                "[2026-03-02 10:20:15] WARN: upstream server slow response",
                "[2026-03-02 10:22:30] WARN: SSL certificate expires in 7 days"
            ]
        },
        "database": {
            "error": [
                "[2026-03-02 10:15:22] ERROR: connection pool exhausted",
                "[2026-03-02 10:18:45] ERROR: deadlock detected"
            ],
            "warning": [
                "[2026-03-02 10:10:00] WARN: slow query detected (>5s)"
            ]
        },
        "vpn": {
            "error": [
                "[2026-03-02 10:30:15] ERROR: authentication failed for user admin",
                "[2026-03-02 10:32:00] ERROR: connection refused"
            ],
            "warning": [
                "[2026-03-02 10:25:00] WARN: multiple failed login attempts"
            ]
        }
    }
    
    logs = mock_logs.get(service.lower(), {}).get(log_type.lower(), 
                [f"No {log_type} logs found for {service}"])
    
    result = f"=== {service.upper()} {log_type.upper()} Logs (last {lines} lines) ===\n"
    result += "\n".join(logs[:lines])
    
    logger.add_observation(f"Retrieved {len(logs)} log entries for {service}", logs[:2])
    return result

@tool
def status_check(target: str, check_type: str = "basic"):
    """
    Check the status of IT infrastructure components.
    
    Args:
        target: The target to check (server name, service name, or component)
        check_type: Type of check (basic, deep, health)
    
    Returns:
        Status information for the target
    """
    logger.add_action("Check Status", "status_check", {"target": target, "check_type": check_type})
    
    # Mock status data
    status_responses = {
        "server-web-01": {
            "basic": "Status: Running | Uptime: 45 days | Load: 0.85",
            "deep": "Status: Running | CPU: 78% | RAM: 82% | Disk: 65% | Network: OK"
        },
        "server-db-01": {
            "basic": "Status: Running | Uptime: 120 days | Load: 0.45",
            "deep": "Status: Running | CPU: 45% | RAM: 67% | Disk: 89% | Connections: 234"
        },
        "vpn-gateway": {
            "basic": "Status: Running | Active Connections: 45",
            "deep": "Status: Running | CPU: 23% | RAM: 34% | Bandwidth: 150Mbps/1Gbps"
        },
        "mail-server": {
            "basic": "Status: Running | Queue: 0",
            "deep": "Status: Running | CPU: 12% | RAM: 45% | Messages/hour: 1250"
        }
    }
    
    target_lower = target.lower()
    if target_lower in status_responses:
        result = f"=== {target.upper()} Status Check ({check_type}) ===\n"
        result += status_responses[target_lower].get(check_type, status_responses[target_lower]["basic"])
    else:
        result = f"Status check for {target}: Unknown target. Available: {', '.join(status_responses.keys())}"
    
    logger.add_observation(f"Status check completed for {target}", result)
    return result

@tool
def server_metrics(server_id: str):
    """
    Get CPU, RAM, and Disk metrics for a specific server.
    
    Args:
        server_id: The server identifier (e.g., 'server-web-01', 'server-db-01')
    
    Returns:
        Current server resource metrics
    """
    logger.add_action("Get Server Metrics", "server_metrics", {"server_id": server_id})
    
    # Mock metrics data
    metrics_data = {
        "server-web-01": {
            "server_id": "server-web-01",
            "cpu_usage": "78%",
            "ram_usage": "82%",
            "disk_usage": "65%",
            "network_in": "45 Mbps",
            "network_out": "120 Mbps",
            "status": "Healthy"
        },
        "server-db-01": {
            "server_id": "server-db-01",
            "cpu_usage": "45%",
            "ram_usage": "67%",
            "disk_usage": "89%",
            "network_in": "12 Mbps",
            "network_out": "8 Mbps",
            "status": "Warning - High disk"
        },
        "server-cache-01": {
            "server_id": "server-cache-01",
            "cpu_usage": "23%",
            "ram_usage": "95%",
            "disk_usage": "12%",
            "network_in": "89 Mbps",
            "network_out": "156 Mbps",
            "status": "Warning - High memory"
        }
    }
    
    if server_id in metrics_data:
        m = metrics_data[server_id]
        result = f"""=== Server Metrics: {server_id} ===
CPU Usage: {m['cpu_usage']}
RAM Usage: {m['ram_usage']}
Disk Usage: {m['disk_usage']}
Network In: {m['network_in']}
Network Out: {m['network_out']}
Overall Status: {m['status']}"""
    else:
        result = f"Server {server_id} not found. Available servers: {', '.join(metrics_data.keys())}"
    
    logger.add_observation(f"Retrieved metrics for {server_id}", metrics_data.get(server_id))
    return result

@tool
def create_ticket(title: str, description: str, priority: str = "medium", category: str = "general"):
    """
    Create an IT support ticket in the ticketing system.
    
    Args:
        title: Brief summary of the issue
        description: Detailed description of the problem
        priority: Ticket priority (low, medium, high, critical)
        category: Ticket category (network, software, hardware, security, general)
    
    Returns:
        Created ticket information with ticket ID
    """
    logger.add_action("Create Support Ticket", "create_ticket", 
                     {"title": title, "priority": priority, "category": category})
    
    # Generate mock ticket ID
    ticket_id = f"IT-{hashlib.md5(f'{title}{datetime.now()}'.encode()).hexdigest()[:8].upper()}"
    
    result = f"""=== Ticket Created Successfully ===
Ticket ID: {ticket_id}
Title: {title}
Priority: {priority.upper()}
Category: {category}
Status: Open
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Description:
{description}

Next Steps:
- Ticket assigned to IT support queue
- You will receive updates via email
- Reference this ticket ID for follow-ups
"""
    
    logger.add_observation(f"Ticket {ticket_id} created successfully", {"ticket_id": ticket_id})
    return result

@tool
def restart_service(service_name: str, server: str = "localhost"):
    """
    Restart a backend service. This is a risky action that requires confirmation.
    
    Args:
        service_name: Name of the service to restart
        server: Server where the service is running (default: localhost)
    
    Returns:
        Result of the restart operation
    """
    logger.add_action("Restart Service", "restart_service", {"service_name": service_name, "server": server})
    
    # Validate the action is safe
    is_valid, message = safety.validate_tool_usage("restart_service", {"service_name": service_name})
    
    if not is_valid:
        logger.add_error(f"Service restart blocked: {message}")
        return f"Action Blocked: {message}"
    
    # Simulate restart
    result = f"""=== Service Restart Initiated ===
Service: {service_name}
Server: {server}
Status: Successfully restarted
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Note: Service restart may cause brief interruption.
Users have been notified.
"""
    
    logger.add_observation(f"Service {service_name} restarted successfully", {"service": service_name})
    return result


@tool
def network_diagnostics(target: str, diagnostic_type: str = "ping"):
    """
    Perform network diagnostics on a target host.
    
    Args:
        target: The target hostname or IP address
        diagnostic_type: Type of diagnostic - "ping", "dns", "traceroute", or "port_check"
    
    Returns:
        Diagnostic results including latency, packet loss, DNS resolution, or port status
    """
    import socket
    import time
    import random
    
    logger.add_action("Running network diagnostics", "network_diagnostics", {"target": target, "type": diagnostic_type})
    
    results = {}
    
    if diagnostic_type == "ping":
        # Simulate ping results
        results = {
            "target": target,
            "type": "ping",
            "packets_sent": 4,
            "packets_received": 4,
            "packet_loss": "0%",
            "min_latency": f"{random.uniform(1, 20):.1f}ms",
            "max_latency": f"{random.uniform(20, 50):.1f}ms",
            "avg_latency": f"{random.uniform(10, 30):.1f}ms",
            "status": "success"
        }
        logger.add_observation("Ping diagnostics completed", results)
        
    elif diagnostic_type == "dns":
        try:
            start = time.time()
            ip = socket.gethostbyname(target)
            elapsed = (time.time() - start) * 1000
            results = {
                "target": target,
                "type": "dns",
                "resolved_ip": ip,
                "resolution_time": f"{elapsed:.2f}ms",
                "status": "success"
            }
        except socket.gaierror as e:
            results = {
                "target": target,
                "type": "dns",
                "error": str(e),
                "status": "failed"
            }
        logger.add_observation("DNS lookup completed", results)
        
    elif diagnostic_type == "traceroute":
        # Simulate traceroute
        hops = []
        for i in range(1, 6):
            hops.append({
                "hop": i,
                "address": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                "rtt": f"{random.uniform(1, 20):.1f}ms"
            })
        results = {
            "target": target,
            "type": "traceroute",
            "hops": hops,
            "total_hops": len(hops),
            "status": "success"
        }
        logger.add_observation("Traceroute completed", results)
        
    elif diagnostic_type == "port_check":
        # Simulate port check
        common_ports = [22, 80, 443, 3306, 5432, 8080]
        port_results = {}
        for port in common_ports:
            port_results[port] = "open" if random.random() > 0.3 else "closed"
        results = {
            "target": target,
            "type": "port_check",
            "ports": port_results,
            "status": "success"
        }
        logger.add_observation("Port scan completed", results)
    
    return f"=== Network Diagnostics Results ===\nTarget: {target}\nType: {diagnostic_type}\n\n{json.dumps(results, indent=2)}"


@tool
def user_management(action: str, username: str = None, server: str = "localhost"):
    """
    Manage user accounts on a server.
    
    Args:
        action: Action to perform - "list", "status", "unlock", "disable", "enable"
        username: Username to manage (required for status/unlock/disable/enable actions)
        server: Target server (default: localhost)
    
    Returns:
        Results of the user management action
    """
    import random
    
    logger.add_action(f"Performing user management: {action}", "user_management", {"action": action, "username": username})
    
    if action == "list":
        users = [
            {"username": "admin", "status": "active", "last_login": "2024-01-15 09:30:00", "role": "administrator"},
            {"username": "jsmith", "status": "active", "last_login": "2024-01-14 16:45:00", "role": "user"},
            {"username": "mjones", "status": "locked", "last_login": "2024-01-10 08:15:00", "role": "user"},
            {"username": "bwilliams", "status": "active", "last_login": "2024-01-15 11:20:00", "role": "user"},
            {"username": "sysop", "status": "disabled", "last_login": "2023-12-01 00:00:00", "role": "system"}
        ]
        return f"=== User List ({server}) ===\n" + "\n".join([f"{u['username']}: {u['status']} (role: {u['role']})" for u in users])
    
    elif action == "status":
        if not username:
            return "Error: Username required for status check"
        
        return f"=== User Status ===\nUsername: {username}\nStatus: {random.choice(['active', 'locked', 'disabled'])}\nLast Login: 2024-01-15 09:30:00\nPassword Expires: 2024-02-15\nMFA Enabled: Yes"
    
    elif action == "unlock":
        if not username:
            return "Error: Username required for unlock"
        
        logger.add_observation(f"User {username} unlocked successfully", {"username": username})
        return f"=== User Unlocked ===\nUsername: {username}\nStatus: Unlocked successfully\nServer: {server}"
    
    elif action == "disable":
        if not username:
            return "Error: Username required for disable"
        
        logger.add_observation(f"User {username} disabled", {"username": username})
        return f"=== User Disabled ===\nUsername: {username}\nStatus: Disabled\nServer: {server}"
    
    elif action == "enable":
        if not username:
            return "Error: Username required for enable"
        
        logger.add_observation(f"User {username} enabled", {"username": username})
        return f"=== User Enabled ===\nUsername: {username}\nStatus: Enabled\nServer: {server}"
    
    return "Error: Unknown action. Use: list, status, unlock, disable, enable"


@tool
def process_management(action: str, process_name: str = None, pid: int = None, server: str = "localhost"):
    """
    Manage processes on a server.
    
    Args:
        action: Action to perform - "list", "kill", "restart", "info"
        process_name: Name of the process (for list/restart)
        pid: Process ID (for kill/info)
        server: Target server (default: localhost)
    
    Returns:
        Results of the process management action
    """
    import random
    
    logger.add_action(f"Performing process management: {action}", "process_management", {"action": action, "process": process_name or pid})
    
    if action == "list":
        processes = [
            {"pid": 1, "name": "systemd", "cpu": 0.1, "memory": 0.3, "status": "running"},
            {"pid": 234, "name": "sshd", "cpu": 0.0, "memory": 0.2, "status": "running"},
            {"pid": 456, "name": "nginx", "cpu": 1.2, "memory": 2.5, "status": "running"},
            {"pid": 789, "name": "postgres", "cpu": 3.4, "memory": 8.2, "status": "running"},
            {"pid": 1024, "name": "python", "cpu": 0.5, "memory": 1.1, "status": "running"},
            {"pid": 2048, "name": "node", "cpu": 2.1, "memory": 4.3, "status": "running"}
        ]
        
        if process_name:
            processes = [p for p in processes if process_name.lower() in p["name"].lower()]
        
        result = f"=== Process List ({server}) ===\n"
        result += "PID     | Name       | CPU%  | Memory% | Status\n"
        result += "-" * 55 + "\n"
        for p in processes:
            result += f"{p['pid']:7} | {p['name']:10} | {p['cpu']:5.1f} | {p['memory']:7.1f} | {p['status']}\n"
        return result
    
    elif action == "kill":
        target = pid or process_name
        if not target:
            return "Error: PID or process name required"
        
        logger.add_observation(f"Process {target} terminated", {"target": target})
        return f"=== Process Terminated ===\nTarget: {target}\nStatus: Successfully terminated\nServer: {server}"
    
    elif action == "restart":
        if not process_name:
            return "Error: Process name required for restart"
        
        logger.add_observation(f"Process {process_name} restarted", {"process_name": process_name})
        return f"=== Process Restarted ===\nProcess: {process_name}\nStatus: Successfully restarted\nServer: {server}"
    
    elif action == "info":
        if not pid:
            return "Error: PID required for info"
        
        return f"=== Process Info ===\nPID: {pid}\nName: sample_process\nCPU: 1.5%\nMemory: 3.2%\nThreads: 8\nUser: root\nUptime: 2d 3h 45m"
    
    return "Error: Unknown action. Use: list, kill, restart, info"


@tool
def ssl_certificate_check(domain: str):
    """
    Check SSL certificate status for a domain.
    
    Args:
        domain: The domain to check (e.g., example.com)
    
    Returns:
        SSL certificate information including validity, expiry, and issuer
    """
    import random
    from datetime import datetime, timedelta
    
    logger.add_action("Checking SSL certificate", "ssl_certificate_check", {"domain": domain})
    
    days_until_expiry = random.randint(-30, 90)
    expiry_date = datetime.now() + timedelta(days=days_until_expiry)
    
    result = f"=== SSL Certificate Check ===\nDomain: {domain}\n"
    result += f"Valid: {'Yes' if days_until_expiry > 0 else 'No - EXPIRED'}\n"
    result += f"Issuer: Let's Encrypt Authority X3\n"
    result += f"Valid From: {(datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d')}\n"
    result += f"Valid Until: {expiry_date.strftime('%Y-%m-%d')}\n"
    result += f"Days Remaining: {days_until_expiry}\n"
    result += f"Protocol: TLS 1.3\n"
    result += f"Cipher: ECDHE-RSA-AES256-GCM-SHA384"
    
    return result


@tool
def email_management(action: str, email_address: str = None):
    """
    Manage email accounts and diagnose email issues.
    
    Args:
        action: Action to perform - "check", "quota", "devices", "rules", "sync"
        email_address: The email address to manage (required for all actions except "sync")
    
    Returns:
        Email account information and status
    """
    import random
    from datetime import datetime, timedelta
    
    logger.add_action(f"Performing email management: {action}", "email_management", {"action": action, "email": email_address})
    
    if action == "check":
        # Check overall email health
        if not email_address:
            return "Error: Email address required for health check"
        
        result = f"=== Email Health Check ===\nEmail: {email_address}\n"
        result += f"Status: Active\n"
        result += f"Last Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        result += f"\n--- Account Status ---\n"
        result += f"Account Active: Yes\n"
        result += f"Password Expires: 2024-03-01\n"
        result += f"MFA Enabled: Yes\n"
        result += f"\n--- Server Status ---\n"
        result += f"IMAP Server: Online\n"
        result += f"SMTP Server: Online\n"
        result += f"Spam Filter: Active\n"
        result += f"\n--- Recent Activity ---\n"
        result += f"Last Login: 2024-01-15 09:30:00\n"
        result += f"Login IP: 192.168.1.100\n"
        result += f"Failed Logins (24h): 0"
        
        logger.add_observation("Email health check completed", {"email": email_address})
        return result
    
    elif action == "quota":
        if not email_address:
            return "Error: Email address required for quota check"
        
        # Simulate mailbox quota
        used_mb = random.randint(500, 4500)
        quota_mb = 5000
        used_percent = (used_mb / quota_mb) * 100
        
        result = f"=== Email Quota Report ===\nEmail: {email_address}\n"
        result += f"\n--- Storage ---\n"
        result += f"Used: {used_mb} MB\n"
        result += f"Quota: {quota_mb} MB\n"
        result += f"Available: {quota_mb - used_mb} MB\n"
        result += f"Usage: {used_percent:.1f}%\n"
        result += f"\n--- Breakdown ---\n"
        result += f"Inbox: {int(used_mb * 0.4)} MB\n"
        result += f"Sent: {int(used_mb * 0.2)} MB\n"
        result += f"Drafts: {int(used_mb * 0.05)} MB\n"
        result += f"Trash: {int(used_mb * 0.1)} MB\n"
        result += f"Archive: {int(used_mb * 0.25)} MB"
        
        if used_percent > 90:
            result += f"\n\n⚠️ WARNING: Mailbox is nearly full. Consider archiving old emails."
        
        logger.add_observation("Email quota check completed", {"email": email_address, "used_mb": used_mb})
        return result
    
    elif action == "devices":
        if not email_address:
            return "Error: Email address required for device check"
        
        devices = [
            {"device": "MacBook Pro", "type": "Desktop", "last_sync": "2024-01-15 09:30:00", "status": "active"},
            {"device": "iPhone 15", "type": "Mobile", "last_sync": "2024-01-15 08:45:00", "status": "active"},
            {"device": "iPad Air", "type": "Tablet", "last_sync": "2024-01-14 22:00:00", "status": "inactive"}
        ]
        
        result = f"=== Synced Devices ===\nEmail: {email_address}\n\n"
        result += "Device          | Type     | Last Sync            | Status\n"
        result += "-" * 65 + "\n"
        for d in devices:
            result += f"{d['device']:16} | {d['type']:8} | {d['last_sync']:19} | {d['status']}\n"
        
        result += f"\nTotal Devices: {len(devices)}\nActive: {sum(1 for d in devices if d['status'] == 'active')}"
        
        logger.add_observation("Email devices check completed", {"email": email_address, "devices": len(devices)})
        return result
    
    elif action == "rules":
        if not email_address:
            return "Error: Email address required for rules check"
        
        rules = [
            {"name": "Move newsletters to Archive", "enabled": True, "priority": 1},
            {"name": "Auto-reply when OOO", "enabled": False, "priority": 2},
            {"name": "Flag emails from manager", "enabled": True, "priority": 3},
            {"name": "Delete spam after 30 days", "enabled": True, "priority": 4}
        ]
        
        result = f"=== Email Rules ===\nEmail: {email_address}\n\n"
        result += "Rule                           | Enabled | Priority\n"
        result += "-" * 55 + "\n"
        for r in rules:
            result += f"{r['name']:30} | {'Yes' if r['enabled'] else 'No':7} | {r['priority']}\n"
        
        logger.add_observation("Email rules check completed", {"email": email_address, "rules": len(rules)})
        return result
    
    elif action == "sync":
        # Global sync status
        result = "=== Email Sync Status ===\n\n"
        result += "--- Server Status ---\n"
        result += "IMAP Server: Online (imap.company.com:993)\n"
        result += "SMTP Server: Online (smtp.company.com:587)\n"
        result += "Exchange Server: Online\n"
        result += "\n--- Sync Queue ---\n"
        result += "Pending Emails: 0\n"
        result += "Failed Syncs: 0\n"
        result += "Last Full Sync: 2024-01-15 09:30:00\n"
        result += "\n--- Active Connections ---\n"
        result += "Webmail: Connected\n"
        result += "Mobile: Connected (3 devices)\n"
        result += "Desktop: Connected (1 device)"
        
        logger.add_observation("Email sync status checked", {"status": "healthy"})
        return result
    
    return "Error: Unknown action. Use: check, quota, devices, rules, or sync"

# Tool list
tools = [kb_search, log_search, status_check, server_metrics, create_ticket, restart_service, network_diagnostics, user_management, process_management, ssl_certificate_check, email_management]
tool_node = ToolNode(tools)



class AgentState(TypedDict):
    """State managed throughout the agent execution"""
    messages: Annotated[List[BaseMessage], "The list of messages in the conversation"]
    thread_id: str
    next_step: str
    requires_confirmation: bool
    confirmation_pending: bool



def safety_check_node(state: AgentState) -> AgentState:
    """Initial safety check for user input"""
    thread_id = state.get("thread_id", "default")
    user_message = state["messages"][-1].content
    
    # Check for prompt injection
    logger.add_thought("Performing safety check on user input")
    
    is_injection, injection_msg = safety.check_prompt_injection(user_message)
    
    if is_injection:
        logger.add_safety("Prompt Injection", injection_msg, passed=False)
        logger.add_reflection("Rejecting malicious input", "end_conversation")
        
        # Add rejection message
        rejection = AIMessage(content="I cannot process that request. It appears to contain potentially harmful instructions. I'm designed to follow safe, legitimate IT support procedures. How can I help you with a genuine IT issue?")
        
        return {
            "messages": state["messages"] + [rejection],
            "next_step": END,
            "requires_confirmation": False,
            "confirmation_pending": False
        }
    
    # Redact any sensitive data from the message
    safe_message = safety.redact_sensitive_data(user_message)
    
    logger.add_safety("Input Validation", "No threats detected", passed=True)
    logger.add_thought(f"Original message: '{user_message}' -> Safe message: '{safe_message}'")
    
    # Add system context from memory
    context = memory.get_context_summary(thread_id)
    
    # Create system message with context
    system_msg = SystemMessage(content=f"""You are Sentinel AI, an expert IT Support Assistant. 
You help users troubleshoot IT issues including VPN, websites, servers, storage, and email.
Be helpful and professional. Ask clarifying questions if needed.

Current conversation context:
{context}""")
    
    # Rebuild messages with system context
    new_messages = [system_msg, HumanMessage(content=safe_message)]
    
    return {
        "messages": new_messages,
        "next_step": "agent",
        "requires_confirmation": False,
        "confirmation_pending": False
    }

def call_model(state: AgentState):
    """Invoke the LLM with tools"""
    logger.add_thought("Invoking LLM with available tools")
    
    # Debug: Check what messages we have
    messages = state['messages']
    logger.add_thought(f"Messages count: {len(messages)}")
    for i, msg in enumerate(messages):
        logger.add_thought(f"Message {i}: {type(msg).__name__} - Content: '{msg.content[:50]}...'")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2
    )
    
    try:
        # Try with tools first
        llm_with_tools = llm.bind_tools(tools)
        response = llm_with_tools.invoke(messages)
    except Exception as e:
        logger.add_error(f"Tool binding failed: {str(e)}", "fallback_to_direct_llm")
        # Fallback to direct LLM without tools
        response = llm.invoke(messages)
    
    # Log LLM decision
    if hasattr(response, 'tool_calls') and response.tool_calls:
        tool_names = [tc['name'] for tc in response.tool_calls]
        logger.add_thought(f"LLM decided to use tools: {tool_names}")
        logger.add_reflection("Tool selection complete", "execute_tools")
    else:
        logger.add_thought("LLM decided to respond directly without tools")
        
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", "confirm", "end"]:
    """Determine next step based on agent response"""
    messages = state['messages']
    last_message = messages[-1]
    
    # Check if there are tool calls
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        # Check if any tool requires confirmation
        for tc in last_message.tool_calls:
            if safety.requires_confirmation(tc['name']):
                logger.add_thought(f"Confirmation required for: {tc['name']}")
                return "confirm"
        return "tools"
    
    return "end"

def handle_confirmation(state: AgentState) -> AgentState:
    """Handle user confirmation for risky actions"""
    # This node would pause for user confirmation
    # For now, we'll proceed but log the need for confirmation
    logger.add_thought("Requesting user confirmation for risky action")
    
    return {
        "next_step": "tools",
        "requires_confirmation": True,
        "confirmation_pending": True
    }

def process_tool_results(state: AgentState):
    """Process tool execution results and generate response"""
    messages = state['messages']
    last_message = messages[-1]
    
    # Get tool results
    if isinstance(last_message, ToolMessage):
        tool_result = last_message.content
        tool_name = last_message.name
        
        logger.add_observation(f"Tool {tool_name} returned result", tool_result[:200])
        
        # Add the tool result to messages for next iteration
        return {"messages": messages}
    
    return {"messages": messages}

def handle_error(state: AgentState, error: Exception) -> AgentState:
    """Handle errors during agent execution"""
    logger.add_error(f"Agent execution error: {str(error)}", "fallback_response")
    
    error_message = AIMessage(
        content=f"I encountered an error while processing your request: {str(error)[:200]}. Let me try an alternative approach."
    )
    
    return {
        "messages": state["messages"] + [error_message],
        "next_step": "agent",
        "requires_confirmation": False,
        "confirmation_pending": False
    }

def save_to_memory(state: AgentState) -> AgentState:
    """Save conversation to memory"""
    thread_id = state.get("thread_id", "default")
    
    if len(state["messages"]) >= 2:
        user_msg = state["messages"][0].content if isinstance(state["messages"][0], HumanMessage) else ""
        # Find the last AI response
        ai_response = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and not hasattr(msg, 'tool_calls'):
                ai_response = msg.content
                break
        
        # Extract tools used
        tools_used = []
        for msg in state["messages"]:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                tools_used.extend([tc['name'] for tc in msg.tool_calls])
        
        memory.add_turn(thread_id, user_msg, ai_response, tools_used)
        logger.add_observation(f"Saved conversation to memory for thread: {thread_id}")
    
    return state



workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("safety_check", safety_check_node)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("confirm", handle_confirmation)
workflow.add_node("memory", save_to_memory)

# Set entry point
workflow.set_entry_point("safety_check")

# Add edges
workflow.add_edge("safety_check", "agent")

# Conditional edges from agent
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "confirm": "confirm",
        "end": "memory"
    }
)

# From confirmation to tools (after user approves)
workflow.add_edge("confirm", "tools")

# From tools back to agent for processing results
workflow.add_edge("tools", "agent")

# From memory to end
workflow.add_edge("memory", END)

# Compile the app
app = workflow.compile()



__all__ = [
    'app',
    'logger', 
    'memory',
    'safety',
    'rag',
    'ObservabilityLogger',
    'ConversationMemory',
    'SafetyController',
    'KnowledgeBaseRAG'
]
