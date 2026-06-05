import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  ShieldAlert, 
  Send, 
  TrendingUp, 
  ExternalLink, 
  Database, 
  ChevronRight,
  RefreshCw
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [funds, setFunds] = useState([]);
  const [selectedFundName, setSelectedFundName] = useState(null);
  const [isDbLoaded, setIsDbLoaded] = useState(false);

  const messagesEndRef = useRef(null);

  // Fetch supported funds from the backend API on mount
  useEffect(() => {
    fetchFunds();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const fetchFunds = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/funds`);
      if (response.ok) {
        const data = await response.json();
        setFunds(data);
        setIsDbLoaded(data.length > 0);
      }
    } catch (error) {
      console.error('Failed to fetch funds from backend:', error);
      setIsDbLoaded(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputText.trim();
    if (!text) return;

    // Clear input if sending from main input bar
    if (!textToSend) {
      setInputText('');
    }

    // Add user message to state
    const newUserMessage = {
      sender: 'user',
      text: text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text }),
      });

      if (!response.ok) {
        throw new Error(`Server returned code ${response.status}`);
      }

      const data = await response.json();
      
      // Highlight the active fund in the sidebar if the response is about a specific fund
      if (data.scheme_name) {
        setSelectedFundName(data.scheme_name);
      }

      // Add assistant response to state
      const newAssistantMessage = {
        sender: 'assistant',
        text: data.response,
        intent: data.intent,
        url: data.url,
        is_fallback: data.is_fallback,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, newAssistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      // Fallback local error message
      const errorMsg = {
        sender: 'assistant',
        text: 'Sorry, I am unable to connect to the backend server. Please make sure that server.py is running on port 8000.',
        intent: 'error',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    handleSendMessage();
  };

  // Helper to extract a friendly host name for the citation pill
  const getDomainName = (urlString) => {
    if (!urlString) return 'Groww';
    try {
      const url = new URL(urlString);
      return url.hostname.replace('www.', '');
    } catch (e) {
      return 'groww.in';
    }
  };

  const quickStartQuestions = [
    "What is the expense ratio and benchmark of HDFC Defence Fund?",
    "Who manages the HDFC Small Cap Fund and what is their tenure?",
    "What are the exit load details of HDFC Gold ETF?"
  ];

  return (
    <div className="app-container">
      {/* 1. Sticky Warning Disclaimer Banner */}
      <div className="sticky-disclaimer">
        <ShieldAlert size={16} />
        <span>
          <strong>Disclaimer:</strong> This assistant is for educational purposes only and does not provide financial advice, investment recommendations, or comparisons.
        </span>
      </div>

      <div className="layout-main">
        {/* 2. Sidebar with Supported Funds */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <h2>
              <TrendingUp size={22} className="text-emerald" />
              <span>Supported Funds</span>
            </h2>
          </div>
          <div className="sidebar-content">
            <div className="fund-list-title">5 HDFC Mutual Fund Schemes</div>
            {funds.map((fund, index) => {
              const isActive = selectedFundName && fund.name.toLowerCase().includes(selectedFundName.toLowerCase().split(' ')[1] || '____');
              const isGold = fund.name.toLowerCase().includes('gold');
              const categoryClass = isGold ? 'commodities' : 'equity';
              
              return (
                <div 
                  key={index} 
                  className={`fund-card ${isActive ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedFundName(fund.name);
                    handleSendMessage(`Tell me about ${fund.name}`);
                  }}
                >
                  <div className="fund-name">{fund.name}</div>
                  <div className="fund-meta">
                    <span className={`fund-badge ${categoryClass}`}>
                      {fund.category}
                    </span>
                    <span className="fund-badge subcat">
                      {fund.sub_category}
                    </span>
                  </div>
                  <div className="fund-nav-row">
                    <span>NAV:</span>
                    <span className="fund-nav-val">₹{fund.nav}</span>
                  </div>
                  <div className="fund-nav-row" style={{ display: 'flex', justifyContent: 'space-between', gap: '8px', fontSize: '11px', marginTop: '6px', borderTop: 'none', paddingTop: 0 }}>
                    <div>
                      <span style={{ color: 'var(--color-text-secondary)' }}>AUM: </span>
                      <span style={{ fontWeight: '500', color: 'var(--color-text-primary)' }}>₹{Math.round(fund.aum || 0).toLocaleString()} Cr</span>
                    </div>
                    <div>
                      <span style={{ color: 'var(--color-text-secondary)' }}>1Y Ret: </span>
                      <span style={{ fontWeight: '600', color: (fund.return_1y || 0) >= 0 ? '#4edea3' : '#ffb4ab' }}>{fund.return_1y || 0}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
            
            {funds.length === 0 && (
              <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                <p style={{ fontSize: '13px', marginBottom: '12px' }}>Loading scheme data...</p>
                <button onClick={fetchFunds} className="quick-start-btn" style={{ padding: '8px 12px', justifyContent: 'center' }}>
                  <RefreshCw size={14} style={{ marginRight: '6px' }} /> Retry Connection
                </button>
              </div>
            )}
          </div>
          <div className="sidebar-footer">
            <div className="status-indicator">
              <span className={`status-dot ${isDbLoaded ? '' : 'offline'}`} style={{ backgroundColor: isDbLoaded ? '#4edea3' : '#ef4444', boxShadow: isDbLoaded ? '0 0 8px #4edea3' : '0 0 8px #ef4444' }}></span>
              <span>{isDbLoaded ? 'Database Online' : 'Database Offline'}</span>
            </div>
          </div>
        </aside>

        {/* 3. Main Chat Area */}
        <main className="chat-container">
          <header className="chat-header">
            <div className="chat-header-info">
              <h1>HDFC Wealth RAG Assistant</h1>
              <p>Secure, facts-only chat validated by programmatic guardrails</p>
            </div>
            <div className="status-indicator" style={{ fontSize: '12px', opacity: 0.8 }}>
              <Database size={14} style={{ marginRight: '4px', color: '#4edea3' }} />
              <span>ChromaDB Vector Store</span>
            </div>
          </header>

          <div className="messages-stream">
            {messages.length === 0 ? (
              // Welcome Screen when no messages are sent
              <div className="welcome-section">
                <div className="welcome-logo">
                  <MessageSquare size={32} />
                </div>
                <h3>Welcome to HDFC Wealth Assistant</h3>
                <p>
                  I am a compliant, facts-only assistant powered by RAG and protected by real-time safety guardrails. Ask about specific scheme facts, expense ratios, NAV, portfolio managers, and more.
                </p>

                <div className="quick-start-title">Suggested Inquiries</div>
                <div className="quick-start-grid">
                  {quickStartQuestions.map((q, idx) => (
                    <button 
                      key={idx} 
                      className="quick-start-btn"
                      onClick={() => handleSendMessage(q)}
                    >
                      <span>{q}</span>
                      <ChevronRight size={16} />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              // Active Message Feed
              messages.map((msg, idx) => (
                <div key={idx} className={`message-wrapper ${msg.sender}`}>
                  <div className={`message-avatar ${msg.sender}`}>
                    {msg.sender === 'user' ? 'U' : 'AI'}
                  </div>
                  <div className="message-bubble">
                    <div className="message-text">{msg.text}</div>
                    
                    {/* Render Citations if provided */}
                    {msg.sender === 'assistant' && msg.url && (
                      <div className="message-footer">
                        <a 
                          href={msg.url} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="citation-badge"
                        >
                          <ExternalLink size={12} />
                          <span>Source: {getDomainName(msg.url)}</span>
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}

            {/* Loading / Typing Indicator */}
            {isLoading && (
              <div className="message-wrapper assistant">
                <div className="message-avatar assistant">AI</div>
                <div className="message-bubble">
                  <div className="typing-indicator">
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                    <div className="typing-dot"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* 4. Chat Input Bar */}
          <div className="input-area">
            <form onSubmit={handleFormSubmit} className="input-wrapper">
              <input
                type="text"
                className="chat-input"
                placeholder="Ask a question about HDFC Mutual Funds..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                disabled={isLoading}
              />
              <button 
                type="submit" 
                className="send-btn"
                disabled={isLoading || !inputText.trim()}
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
