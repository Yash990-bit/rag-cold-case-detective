import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Search, FileText, Pin, Cpu, MessageSquare, Clock } from 'lucide-react';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Welcome, Detective. The evidence files are loaded. What's on your mind regarding Case 2023-CF-992?" }
  ]);
  const [input, setInput] = useState('');
  const [sources, setSources] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeView, setActiveView] = useState('board'); // 'board' or 'timeline'
  const [serverStatus, setServerStatus] = useState('connecting'); // 'connected', 'error', 'connecting'
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    checkHealth();
    fetchTimeline();

    // Poll health every 10 seconds
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      await axios.get(`${API_BASE_URL}/health`);
      setServerStatus('connected');
    } catch (error) {
      setServerStatus('error');
    }
  };

  const fetchTimeline = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/timeline`);
      setTimeline(response.data.timeline);
    } catch (error) {
      console.error('Error fetching timeline:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, { message: input });

      setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);

      // Update Case Board with new sources
      setSources(prev => {
        const newSources = response.data.sources;
        const combined = [...newSources, ...prev];
        const unique = Array.from(new Set(combined.map(s => s.source)))
          .map(source => combined.find(s => s.source === source));
        return unique.slice(0, 9);
      });

      // Refresh timeline after each query in case new details were found (though currently static)
      fetchTimeline();
    } catch (error) {
      console.error('Error calling API:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I lost my connection to the database. Is the API server running?' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <div className="bg-mesh" />

      {/* Sidebar: Chat */}
      <aside className="sidebar glass">
        <div className="chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexGrow: 1 }}>
            <Cpu className="text-accent-blue" size={24} />
            <h2>Detective AI</h2>
          </div>
          <div className="status-indicator" title={`Server Status: ${serverStatus}`}>
            <span className={`status-dot ${serverStatus}`} />
            <span className="status-text">{serverStatus}</span>
          </div>
        </div>

        <div className="chat-messages" ref={scrollRef}>
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`message ${msg.role}`}
              >
                {msg.content}
              </motion.div>
            ))}
          </AnimatePresence>
          {isLoading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="message assistant">
              Searching files...
            </motion.div>
          )}
        </div>

        <div className="chat-input-container">
          <input
            type="text"
            className="chat-input"
            placeholder="Search evidence..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          />
          <button className="send-btn glow-hover" onClick={handleSend} disabled={isLoading}>
            <Send size={18} />
          </button>
        </div>
      </aside>

      {/* Main Area: Case Board / Timeline */}
      <main className="main-board glass">
        <header className="board-header">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{ fontSize: '1.8rem', marginBottom: '4px' }}>
                {activeView === 'board' ? 'Case Board' : "Detective's Timeline"}
              </h1>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Active Case: The Warehouse Incident</p>
            </div>

            <div className="view-toggle">
              <button
                className={`toggle-btn ${activeView === 'board' ? 'active' : ''}`}
                onClick={() => setActiveView('board')}
              >
                Board
              </button>
              <button
                className={`toggle-btn ${activeView === 'timeline' ? 'active' : ''}`}
                onClick={() => setActiveView('timeline')}
              >
                Timeline
              </button>
            </div>
          </div>
        </header>

        <div className="board-grid">
          {activeView === 'board' ? (
            sources.length === 0 ? (
              <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '100px', color: 'var(--text-secondary)' }}>
                <FileText size={48} style={{ marginBottom: '16px', opacity: 0.3 }} />
                <p>Ask a question to pin evidence to the board.</p>
              </div>
            ) : (
              <AnimatePresence mode="popLayout">
                {sources.map((src, i) => (
                  <motion.div
                    key={src.source}
                    layout
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    whileHover={{ scale: 1.02 }}
                    className="evidence-card glass glow-hover"
                  >
                    <div className="pin" />
                    <span className="card-tag">{src.source.replace('.txt', '').replace('_', ' ')}</span>
                    <h3 className="card-title">Evidence File</h3>
                    <p className="card-content">{src.content.substring(0, 150)}...</p>
                  </motion.div>
                ))}
              </AnimatePresence>
            )
          ) : (
            <div className="timeline-container" style={{ gridColumn: '1/-1' }}>
              <AnimatePresence>
                {timeline.map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="timeline-item"
                  >
                    <div className="timeline-marker" />
                    <div className="timeline-connector" />
                    <div className="timeline-content">
                      <div className="timeline-time">{item.time}</div>
                      <div className="timeline-event">{item.event}</div>
                      <div className="timeline-source">Source: {item.source}</div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
