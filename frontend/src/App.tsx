import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import {
  Send,
  Bot,
  Activity,
  ShieldAlert,
  CheckCircle2,
  Terminal,
  Search,
  AlertTriangle,
  Zap,
  Database,
  FileText,
  Check,
  X,
  Brain,
  Eye
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}


interface Message {
  id: number
  type: 'user' | 'bot' | 'system'
  content: string
  timestamp: string
  tool_used?: string
}

interface LogEntry {
  timestamp: string
  category: 'THOUGHT' | 'ACTION' | 'OBSERVATION' | 'REFLECTION' | 'SAFETY' | 'ERROR' | 'SYSTEM'
  message: string
  status: 'processing' | 'success' | 'error' | 'warning'
  metadata?: Record<string, any>
}

interface Confirmation {
  tool_name: string
  parameters: Record<string, any>
  message: string
}

export default function SupportDashboard() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, type: 'bot', content: 'Sentinel AI v2.0 Initialized...\n\nAgentic reasoning loop active.\nSafety controls enabled.\nMemory system online.\n\nHow can I assist you with IT support today?', timestamp: new Date().toLocaleTimeString() }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [reasoningLogs, setReasoningLogs] = useState<LogEntry[]>([
    { timestamp: new Date().toISOString(), category: 'SYSTEM', message: 'Agent loop standby...', status: 'success' },
    { timestamp: new Date().toISOString(), category: 'SYSTEM', message: 'Sentinel AI v2.0 ready', status: 'success' }
  ])
  const [metrics, setMetrics] = useState({ cpu: 0, memory: '0GB/0GB', memory_percent: 0, disk: 0 })
  const [latency, setLatency] = useState(0)
  const [confirmation, setConfirmation] = useState<Confirmation | null>(null)
  const [threadId] = useState('thread-' + Math.random().toString(36).substr(2, 9))

  // Fetch real metrics from backend
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const start = Date.now()
        const response = await axios.get('http://127.0.0.1:8000/metrics')
        const latencyMs = Date.now() - start
        setMetrics(response.data)
        setLatency(latencyMs)
      } catch (error) {
        console.error('Failed to fetch metrics:', error)
      }
    }
    
    fetchMetrics()
    const interval = setInterval(fetchMetrics, 3000)
    return () => clearInterval(interval)
  }, [])

  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addLog = (log: LogEntry) => {
    setReasoningLogs(prev => [...prev, { ...log, id: Date.now() } as any])
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = { 
      id: Date.now(), 
      type: 'user', 
      content: input, 
      timestamp: new Date().toLocaleTimeString() 
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)
    setConfirmation(null)

    // Add initial log
    addLog({
      timestamp: new Date().toISOString(),
      category: 'THOUGHT',
      message: `Processing user query: "${input.substring(0, 50)}..."`,
      status: 'processing'
    })

    try {
      const start = Date.now()
      const response = await axios.post('http://127.0.0.1:8000/chat', {
        message: input,
        thread_id: threadId
      })

      const requestTime = Date.now() - start
      const data = response.data

      // Process and add reasoning logs from backend
      if (data.logs && Array.isArray(data.logs)) {
        const newLogs: LogEntry[] = data.logs.map((l: any) => ({
          timestamp: l.timestamp || new Date().toISOString(),
          category: l.category || 'SYSTEM',
          message: l.message,
          status: l.status || 'success',
          metadata: l.metadata
        }))
        setReasoningLogs(newLogs)
      }

      // Add response time log
      addLog({
        timestamp: new Date().toISOString(),
        category: 'SYSTEM',
        message: `Request completed in ${requestTime}ms`,
        status: 'success'
      })

      // Check if confirmation is required
      if (data.metadata?.requires_confirmation) {
        setConfirmation({
          tool_name: 'restart_service',
          parameters: {},
          message: 'The agent wants to restart a service. Please confirm.'
        })
      }

      setMessages(prev => [...prev, {
        id: Date.now() + 100,
        type: 'bot',
        content: data.response || 'No response received',
        timestamp: new Date().toLocaleTimeString()
      }])

    } catch (error: any) {
      console.error('Chat Error:', error)
      addLog({
        timestamp: new Date().toISOString(),
        category: 'ERROR',
        message: `Request failed: ${error.message}`,
        status: 'error'
      })
      setMessages(prev => [...prev, {
        id: Date.now() + 100,
        type: 'bot',
        content: `Error: ${error.response?.data?.response || error.message || 'Failed to connect to Sentinel AI backend. Please check if the server is running on port 8001.'}`,
        timestamp: new Date().toLocaleTimeString()
      }])
    } finally {
      setIsTyping(false)
    }
  }

  const handleConfirmation = async (approved: boolean) => {
    if (!confirmation) return

    setIsTyping(true)
    
    try {
      const response = await axios.post('http://127.0.0.1:8000/confirm', {
        thread_id: threadId,
        tool_name: confirmation.tool_name,
        approved: approved,
        parameters: confirmation.parameters
      })

      setMessages(prev => [...prev, {
        id: Date.now() + 100,
        type: 'bot',
        content: response.data.response,
        timestamp: new Date().toLocaleTimeString()
      }])

      addLog({
        timestamp: new Date().toISOString(),
        category: 'SAFETY',
        message: `Action ${approved ? 'approved' : 'denied'} by user`,
        status: 'success'
      })

    } catch (error: any) {
      setMessages(prev => [...prev, {
        id: Date.now() + 100,
        type: 'bot',
        content: `Confirmation error: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      }])
    } finally {
      setConfirmation(null)
      setIsTyping(false)
    }
  }

  const getLogIcon = (category: string) => {
    switch (category) {
      case 'THOUGHT': return <Brain size={12} className="text-purple-400" />
      case 'ACTION': return <Zap size={12} className="text-amber-400" />
      case 'OBSERVATION': return <Eye size={12} className="text-blue-400" />
      case 'REFLECTION': return <Search size={12} className="text-green-400" />
      case 'SAFETY': return <ShieldAlert size={12} className="text-orange-400" />
      case 'ERROR': return <AlertTriangle size={12} className="text-red-400" />
      default: return <Terminal size={12} className="text-white/40" />
    }
  }

  const getLogColor = (category: string) => {
    switch (category) {
      case 'THOUGHT': return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      case 'ACTION': return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
      case 'OBSERVATION': return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'REFLECTION': return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'SAFETY': return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'ERROR': return 'bg-red-500/20 text-red-400 border-red-500/30'
      default: return 'bg-white/10 text-white/50 border-white/10'
    }
  }

  return (
    <div className="flex h-screen w-full bg-[#09090b] text-white font-sans overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 border-r border-white/10 glass flex flex-col">
        <div className="p-6 border-b border-white/5">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Activity className="text-blue-500 w-6 h-6 animate-pulse" />
            <span className="gradient-text">SENTINEL AI</span>
          </h1>
          <p className="text-xs text-white/40 mt-1 uppercase tracking-widest">Agentic IT Support v2.0</p>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-all font-medium">
            <Bot size={18} /> Chat Assistant
          </button>
          <div className="px-4 py-2 text-[10px] text-white/30 uppercase tracking-wider">
            Agent Capabilities
          </div>
          <div className="space-y-1 px-4">
            <div className="flex items-center gap-2 text-xs text-white/50 py-1">
              <Brain size={12} className="text-purple-400" /> Reasoning Loop
            </div>
            <div className="flex items-center gap-2 text-xs text-white/50 py-1">
              <Database size={12} className="text-amber-400" /> RAG Knowledge
            </div>
            <div className="flex items-center gap-2 text-xs text-white/50 py-1">
              <FileText size={12} className="text-blue-400" /> 6 Tools
            </div>
            <div className="flex items-center gap-2 text-xs text-white/50 py-1">
              <ShieldAlert size={12} className="text-orange-400" /> Safety Controls
            </div>
          </div>
        </nav>

        <div className="p-4 border-t border-white/5 bg-white/5 mx-2 mb-2 rounded-xl">
          <h3 className="text-[10px] uppercase text-white/40 font-bold mb-3 tracking-wider">System Metrics</h3>
          <div className="space-y-3">
            <MetricItem label="CPU" value={metrics.cpu + "%"} color={metrics.cpu > 80 ? "bg-red-500" : "bg-green-500"} percent={Math.min(metrics.cpu, 100) + "%"} />
            <MetricItem label="MEM" value={metrics.memory} color={metrics.memory_percent > 80 ? "bg-red-500" : "bg-blue-400"} percent={Math.min(metrics.memory_percent, 100) + "%"} />
            <MetricItem label="LAT" value={latency + "ms"} color={latency > 100 ? "bg-red-500" : "bg-purple-500"} percent={Math.min(latency / 2, 100) + "%"} />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="h-16 glass-blue border-b border-blue-500/10 flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-4 text-sm text-white/70">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
              Core System: Online
            </span>
            <span className="w-px h-4 bg-white/10"></span>
            <span className="flex items-center gap-2">Thread: <span className="text-white font-mono text-xs">{threadId.substring(0, 12)}</span></span>
          </div>
          <div className="flex gap-2">
            <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-xs">
              <ShieldAlert size={12} /> Safety: Active
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Chat Panel */}
          <section className="flex-1 flex flex-col bg-[#0b0b0e] border-r border-white/5">
            <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar scroll-smooth">
              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    className={cn(
                      "flex max-w-[85%] group",
                      msg.type === 'user' ? "ml-auto flex-row-reverse" : "flex-row"
                    )}
                  >
                    <div className={cn(
                      "w-8 h-8 rounded-lg flex items-center justify-center shrink-0 shadow-lg",
                      msg.type === 'user' ? "ml-3 bg-purple-600/20 text-purple-400 border border-purple-500/30" : 
                      msg.type === 'system' ? "ml-3 bg-orange-600/20 text-orange-400 border border-orange-500/30" :
                      "mr-3 bg-blue-600/20 text-blue-400 border border-blue-500/30"
                    )}>
                      {msg.type === 'user' ? 'U' : msg.type === 'system' ? '!' : <Bot size={16} />}
                    </div>
                    <div>
                      <div className={cn(
                        "p-4 rounded-2xl shadow-xl transition-all duration-300",
                        msg.type === 'user'
                          ? "bg-purple-600/10 text-purple-50 border border-purple-500/20 rounded-tr-none hover:bg-purple-600/15"
                          : msg.type === 'system'
                          ? "bg-orange-600/10 text-orange-50 border border-orange-500/20 rounded-tr-none"
                          : "bg-white/5 text-white/90 border border-white/10 rounded-tl-none hover:bg-white/10"
                      )}>
                        <p className="text-[14.5px] leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                      </div>
                      <div className={cn(
                        "flex items-center gap-2 mt-1.5 px-1",
                        msg.type === 'user' ? "justify-end" : "justify-start"
                      )}>
                        <span className="text-[10px] text-white/30 font-medium uppercase tracking-tighter italic">{msg.timestamp}</span>
                        <CheckCircle2 size={10} className="text-green-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
              {isTyping && (
                <div className="flex items-center gap-3 text-blue-400/50">
                  <div className="w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center">
                    <Bot size={16} className="animate-spin-slow" />
                  </div>
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400/40 animate-bounce delay-75"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400/40 animate-bounce delay-150"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400/40 animate-bounce delay-300"></span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-white/10 glass">
              <div className="max-w-4xl mx-auto flex gap-3 p-1.5 rounded-2xl bg-white/5 border border-white/10 focus-within:border-blue-500/50 transition-all duration-300">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && !isTyping && handleSend()}
                  placeholder="Describe your IT issue..."
                  className="flex-1 bg-transparent border-none outline-none px-4 py-2 text-[15px] placeholder:text-white/20"
                  disabled={isTyping}
                />
                <button
                  onClick={handleSend}
                  disabled={isTyping || !input.trim()}
                  className="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 text-white flex items-center justify-center shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all active:scale-95 disabled:opacity-50"
                >
                  <Send size={18} />
                </button>
              </div>
              <div className="flex items-center justify-center gap-4 mt-3">
                <p className="text-[10px] text-white/20 uppercase tracking-wider font-medium">Multi-Step Reasoning • Safety Controls • Memory Active</p>
              </div>
            </div>
          </section>

          {/* Observatory Panel - Reasoning Logs */}
          <aside className="w-96 glass flex flex-col">
            <div className="p-4 border-b border-white/10 bg-white/5 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                <Terminal size={14} className="text-purple-400" /> Observatory
              </h2>
              <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">
                {reasoningLogs.length} steps
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar bg-black/20">
              <AnimatePresence>
                {reasoningLogs.map((log, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.02 }}
                    className="p-3 rounded-lg border border-white/10 bg-white/5 flex flex-col gap-2 group hover:border-purple-500/30 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className={cn(
                        "text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0 flex items-center gap-1",
                        getLogColor(log.category)
                      )}>
                        {getLogIcon(log.category)}
                        {log.category}
                      </span>
                      {log.status === 'processing' ? (
                        <div className="flex gap-1">
                          <span className="w-1 h-1 rounded-full bg-purple-400 animate-pulse"></span>
                          <span className="w-1 h-1 rounded-full bg-purple-400 animate-pulse delay-100"></span>
                        </div>
                      ) : log.status === 'error' ? (
                        <AlertTriangle size={10} className="text-red-500" />
                      ) : (
                        <CheckCircle2 size={10} className="text-green-500/50" />
                      )}
                    </div>
                    <p className="text-[11px] leading-relaxed text-white/70 font-mono">
                      {log.message}
                    </p>
                    {log.metadata && Object.keys(log.metadata).length > 0 && (
                      <div className="text-[10px] text-white/40 font-mono mt-1">
                        {log.metadata.tool && (
                          <span className="text-amber-400">Tool: {log.metadata.tool}</span>
                        )}
                        {log.metadata.inputs && (
                          <span className="ml-2 text-blue-400">Inputs: {JSON.stringify(log.metadata.inputs).substring(0, 50)}</span>
                        )}
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            {/* Confirmation Panel */}
            <div className="p-4 border-t border-white/10 space-y-4">
              {confirmation ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/20"
                >
                  <div className="flex items-center gap-2 mb-3 text-orange-400">
                    <ShieldAlert size={16} />
                    <span className="text-xs font-bold uppercase tracking-wider">Action Requires Confirmation</span>
                  </div>
                  <p className="text-xs text-orange-200/70 mb-4 leading-relaxed">
                    The agent is requesting to perform a potentially risky operation. 
                    Please confirm if you want to proceed.
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleConfirmation(true)}
                      className="flex-1 py-2 bg-green-600 hover:bg-green-500 text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      <Check size={14} /> APPROVE
                    </button>
                    <button 
                      onClick={() => handleConfirmation(false)}
                      className="flex-1 py-2 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                      <X size={14} /> DENY
                    </button>
                  </div>
                </motion.div>
              ) : (
                <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                  <div className="flex items-center gap-2 text-green-400 text-xs">
                    <ShieldAlert size={12} />
                    <span>Safety protocols active</span>
                  </div>
                  <p className="text-[10px] text-white/40 mt-1">
                    Prompt injection detection • Tool validation • Confirmation for risky actions
                  </p>
                </div>
              )}
            </div>
          </aside>
        </div>
      </main>
    </div>
  )
}

function MetricItem({ label, value, color, percent }: { label: string, value: string, color: string, percent: string }) {
  return (
    <div className="space-y-1.5 leading-none">
      <div className="flex justify-between text-[10px]">
        <span className="text-white/60 font-medium px-0.5">{label}</span>
        <span className="text-white font-mono">{value}</span>
      </div>
      <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: percent }}
          transition={{ duration: 1, ease: 'easeOut' }}
          className={cn("h-full", color)}
        ></motion.div>
      </div>
    </div>
  )
}
