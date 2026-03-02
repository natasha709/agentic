import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import {
  Send,
  Bot,
  Activity,
  ShieldAlert,
  CheckCircle2,
  Terminal,
  Search
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export default function SupportDashboard() {
  const [messages, setMessages] = useState([
    { id: 1, type: 'bot', content: 'Agent Initialized... System Ready. How can I assist you with IT support today?', timestamp: new Date().toLocaleTimeString() }
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
const [reasoningLogs, setReasoningLogs] = useState([
    { id: 1, label: 'SYSTEM', message: 'Agent loop standby...', status: 'idle' },
    { id: 2, label: 'GRAPH', message: 'Initialized LangGraph state machine', status: 'success' }
  ])
  const [metrics, setMetrics] = useState({ cpu: 0, memory: '0GB/0GB', memory_percent: 0 })
  const [latency, setLatency] = useState(0)

  // Fetch real metrics from backend
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const start = Date.now()
        const response = await axios.get('http://localhost:8001/metrics')
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

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = { id: Date.now(), type: 'user', content: input, timestamp: new Date().toLocaleTimeString() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsTyping(true)

    try {
      // Simulate Reasoning Start Log
      const initialLog = { id: Date.now(), label: 'SYSTEM', message: `Initializing agent for query: "${input}"`, status: 'processing' }
      setReasoningLogs(prev => [...prev, initialLog])

      // Actual Backend Call
const response = await axios.post('http://localhost:8001/chat', {
        message: input,
        thread_id: 'demo-thread-001'
      })

      const data = response.data

      // Update Reasoning Logs with backend steps
      if (data.logs) {
        setReasoningLogs(prev => [...prev, ...data.logs.map((l: any, i: number) => ({
          ...l,
          id: Date.now() + i + 1,
          status: 'success'
        }))])
      }

      setMessages(prev => [...prev, {
        id: Date.now() + 100,
        type: 'bot',
        content: data.response,
        timestamp: new Date().toLocaleTimeString()
      }])

    } catch (error) {
      console.error('Chat Error:', error)
      setMessages(prev => [...prev, {
        id: Date.now() + 100,
        type: 'bot',
content: "Oops! I encountered an error connecting to the Sentinel-AI backend. Please check if the server is running on port 8001.",
        timestamp: new Date().toLocaleTimeString()
      }])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className="flex h-screen w-full bg-[#09090b] text-white font-sans overflow-hidden">
      {/* Sidebar - Navigation/System Status */}
      <div className="w-64 border-r border-white/10 glass flex flex-col">
        <div className="p-6 border-b border-white/5">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Activity className="text-blue-500 w-6 h-6 animate-pulse" />
            <span className="gradient-text">SENTINEL AI</span>
          </h1>
          <p className="text-xs text-white/40 mt-1 uppercase tracking-widest">IT Agentic v1.0.4</p>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20 hover:bg-blue-500/20 transition-all font-medium">
            <Bot size={18} /> Chat Assistant
          </button>
        </nav>

<div className="p-4 border-t border-white/5 bg-white/5 mx-2 mb-2 rounded-xl">
          <h3 className="text-[10px] uppercase text-white/40 font-bold mb-3 tracking-wider">Metrics Monitoring</h3>
<div className="space-y-3">
            <MetricItem label="CPU" value={metrics.cpu + "%"} color={metrics.cpu > 80 ? "bg-red-500" : "bg-green-500"} percent={Math.min(metrics.cpu, 100) + "%"} />
            <MetricItem label="MEM" value={metrics.memory} color={metrics.memory_percent > 80 ? "bg-red-500" : "bg-blue-400"} percent={Math.min(metrics.memory_percent, 100) + "%"} />
            <MetricItem label="LAT" value={latency + "ms"} color={latency > 100 ? "bg-red-500" : "bg-purple-500"} percent={Math.min(latency / 2, 100) + "%"} />
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative">
        {/* Top Header */}
        <header className="h-16 glass-blue border-b border-blue-500/10 flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-4 text-sm text-white/70">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
              Core System: Online
            </span>
            <span className="w-px h-4 bg-white/10"></span>
            <span className="flex items-center gap-2">Thread: <span className="text-white">tx_9422_support</span></span>
          </div>
          <div className="flex gap-2">
            <button className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-white/70 transition-colors">
              <Search size={18} />
            </button>
          </div>
        </header>

        {/* Dynamic Layout: Chat + Reasoning Log */}
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
                      msg.type === 'user' ? "ml-3 bg-purple-600/20 text-purple-400 border border-purple-500/30" : "mr-3 bg-blue-600/20 text-blue-400 border border-blue-500/30"
                    )}>
                      {msg.type === 'user' ? 'U' : <Bot size={16} />}
                    </div>
                    <div>
                      <div className={cn(
                        "p-4 rounded-2xl shadow-xl transition-all duration-300",
                        msg.type === 'user'
                          ? "bg-purple-600/10 text-purple-50 border border-purple-500/20 rounded-tr-none hover:bg-purple-600/15"
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

            {/* Input Bar */}
            <div className="p-4 border-t border-white/10 glass">
              <div className="max-w-4xl mx-auto flex gap-3 p-1.5 rounded-2xl bg-white/5 border border-white/10 focus-within:border-blue-500/50 transition-all duration-300">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                  placeholder="Ask for support or diagnostics..."
                  className="flex-1 bg-transparent border-none outline-none px-4 py-2 text-[15px] placeholder:text-white/20"
                />
                <button
                  onClick={handleSend}
                  className="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-500 text-white flex items-center justify-center shadow-[0_0_20px_rgba(37,99,235,0.4)] transition-all active:scale-95"
                >
                  <Send size={18} />
                </button>
              </div>
              <p className="text-[10px] text-white/20 text-center mt-3 uppercase tracking-wider font-medium">Multi-Step reasoning active • Human-in-the-loop safety protocol (SOP-001)</p>
            </div>
          </section>

          {/* Reasoning Log Panel - The "Wired" part */}
          <aside className="w-80 glass flex flex-col">
            <div className="p-4 border-b border-white/10 bg-white/5 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-widest flex items-center gap-2">
                <Terminal size={14} className="text-purple-400" /> Observatory
              </h2>
              <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">LOGS: ACTIVE</span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-black/20">
              <AnimatePresence>
                {reasoningLogs.map((log) => (
                  <motion.div
                    key={log.id}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-3 rounded-lg border border-white/10 bg-white/5 flex flex-col gap-2 group hover:border-purple-500/30 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className={cn(
                        "text-[9px] font-bold px-1.5 py-0.5 rounded shrink-0",
                        log.label === 'REASONING' ? "bg-purple-500/20 text-purple-400" :
                          log.label === 'TOOL' ? "bg-amber-500/20 text-amber-400" :
                            log.label === 'OBSERVATION' ? "bg-blue-500/20 text-blue-400" :
                              "bg-white/10 text-white/50"
                      )}>
                        {log.label}
                      </span>
                      {log.status === 'processing' ? (
                        <div className="flex gap-1">
                          <span className="w-1 h-1 rounded-full bg-purple-400 animate-pulse"></span>
                          <span className="w-1 h-1 rounded-full bg-purple-400 animate-pulse delay-100"></span>
                        </div>
                      ) : (
                        <CheckCircle2 size={10} className="text-green-500/50" />
                      )}
                    </div>
                    <p className="text-[11px] leading-relaxed text-white/70 font-mono italic">
                      {log.message}
                    </p>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>

            <div className="p-4 border-t border-white/10 space-y-4">
              {messages.length > 0 && messages[messages.length - 1].content.toLowerCase().includes('restart') && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-3 rounded-xl bg-orange-500/10 border border-orange-500/20"
                >
                  <div className="flex items-center gap-2 mb-2 text-orange-400">
                    <ShieldAlert size={14} />
                    <span className="text-[10px] font-bold uppercase tracking-wider">Awaiting Confirmation</span>
                  </div>
                  <p className="text-[11px] text-orange-200/70 mb-3 leading-relaxed">Agent requested critical action: [Restart Service/Server]</p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setMessages(prev => [...prev, { id: Date.now(), type: 'bot', content: "Action Approved. Restarting service now...", timestamp: new Date().toLocaleTimeString() }])}
                      className="flex-1 py-1.5 bg-orange-600 hover:bg-orange-500 text-white text-[10px] font-bold rounded-lg transition-colors"
                    >
                      APPROVE
                    </button>
                    <button className="flex-1 py-1.5 bg-white/10 hover:bg-white/20 text-white/70 text-[10px] font-bold rounded-lg transition-colors">DENY</button>
                  </div>
                </motion.div>
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
