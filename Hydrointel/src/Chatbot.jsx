import React, { useState, useRef, useEffect, useCallback } from "react";
import './index.css';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! Ask me about groundwater levels 🌊", timestamp: new Date() }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [isLoadingFromHistory, setIsLoadingFromHistory] = useState(false);
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [conversationId, setConversationId] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [useWebSocket, setUseWebSocket] = useState(true);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const handleSendRef = useRef(null);
  const wsRef = useRef(null);

  // API Configuration
  const API_BASE_URL = 'http://127.0.0.1:8002';
  const WS_BASE_URL = 'ws://127.0.0.1:8002';

  // Initialize conversation ID
  useEffect(() => {
    if (!conversationId) {
      const newConvId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setConversationId(newConvId);
    }
  }, [conversationId]);

  // WebSocket connection management
  useEffect(() => {
    if (!useWebSocket || !conversationId) return;

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(`${WS_BASE_URL}/ws/${conversationId}`);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('WebSocket connected');
          setConnectionStatus('connected');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('Received WebSocket message:', data);

            if (data.type === 'typing') {
              setIsTyping(data.isTyping);
            } else if (data.type === 'message') {
              const botMessage = {
                sender: 'bot',
                text: data.message,
                timestamp: new Date(data.timestamp)
              };
              setMessages(prev => [...prev, botMessage]);
              setIsTyping(false);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setConnectionStatus('disconnected');
          setIsTyping(false);
          
          // Attempt to reconnect after 3 seconds
          setTimeout(() => {
            if (wsRef.current?.readyState === WebSocket.CLOSED) {
              connectWebSocket();
            }
          }, 3000);
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setConnectionStatus('error');
          setIsTyping(false);
        };

      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        setConnectionStatus('error');
      }
    };

    connectWebSocket();

    // Cleanup function
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [conversationId, useWebSocket]);

  // Initialize speech recognition once
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'en-US';

      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        if (handleSendRef.current) handleSendRef.current(transcript);
      };

      recognitionInstance.onend = () => setIsListening(false);
      setRecognition(recognitionInstance);
    }
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Save conversation to history
  useEffect(() => {
    if (isLoadingFromHistory) {
      setIsLoadingFromHistory(false);
      return;
    }
    
    if (messages.length > 1 && messages[messages.length - 1].sender === "bot") {
      const lastUserMessage = messages.slice().reverse().find(msg => msg.sender === "user");
      if (lastUserMessage) {
        const title = lastUserMessage.text.length > 30 ? lastUserMessage.text.substring(0, 30) + "..." : lastUserMessage.text;
        setConversationHistory(prev => {
          const exists = prev.find(conv => 
            conv.title === title && 
            conv.messages.length === messages.length &&
            conv.messages[conv.messages.length - 1]?.text === messages[messages.length - 1]?.text
          );
          if (!exists) {
            return [{ id: Date.now(), title, messages: [...messages], timestamp: new Date(), conversationId }, ...prev.slice(0, 9)];
          }
          return prev;
        });
      }
    }
  }, [messages, isLoadingFromHistory, conversationId]);

  // Send message via REST API (fallback)
  const sendViaREST = async (messageText) => {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          conversation_id: conversationId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const botMessage = {
        sender: 'bot',
        text: data.response,
        timestamp: new Date(data.timestamp)
      };
      
      setMessages(prev => [...prev, botMessage]);
      setIsTyping(false);

    } catch (error) {
      console.error('REST API error:', error);
      const errorMessage = {
        sender: 'bot',
        text: 'Sorry, I\'m having trouble connecting to the server. Please check if the TaskWeaver backend is running on port 8002.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsTyping(false);
    }
  };

  // Send message via WebSocket
  const sendViaWebSocket = (messageText) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const messageData = {
        message: messageText,
        timestamp: new Date().toISOString()
      };
      wsRef.current.send(JSON.stringify(messageData));
      return true;
    }
    return false;
  };

  const loadConversation = (conv) => {
    setIsLoadingFromHistory(true);
    setSelectedConversation(conv);
    setMessages(conv.messages);
    setConversationId(conv.conversationId);
  };

  const startNewConversation = () => {
    setSelectedConversation(null);
    setMessages([{ sender: "bot", text: "Hello! Ask me about groundwater levels 🌊", timestamp: new Date() }]);
    setInput("");
    const newConvId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setConversationId(newConvId);
  };

  const handleSend = useCallback(async (text) => {
    const messageText = text ?? input;
    if (!messageText.trim()) return;

    const newMessage = { sender: "user", text: messageText, timestamp: new Date() };
    setMessages(prev => [...prev, newMessage]);
    setInput("");
    setIsTyping(true);

    // Try WebSocket first, fall back to REST
    if (useWebSocket && !sendViaWebSocket(messageText)) {
      console.log('WebSocket failed, falling back to REST API');
      await sendViaREST(messageText);
    } else if (!useWebSocket) {
      await sendViaREST(messageText);
    }
  }, [input, conversationId, useWebSocket]);

  // Keep ref updated so recognition callback uses latest handler
  useEffect(() => { 
    handleSendRef.current = handleSend; 
  }, [handleSend]);

  const toggleVoiceRecognition = () => {
    if (!recognition) return;
    if (isListening) recognition.stop();
    else recognition.start();
    setIsListening(!isListening);
  };

  const toggleSidebar = () => {
    setIsSidebarVisible(!isSidebarVisible);
  };

  const toggleConnectionType = () => {
    setUseWebSocket(!useWebSocket);
  };

  // Function to format text with markdown-style formatting
  const formatText = (text) => {
    if (!text) return '';
    
    // Split text into paragraphs
    const paragraphs = text.split('\n\n').filter(p => p.trim());
    
    return paragraphs.map((paragraph, index) => {
      // Handle bold text (**text**)
      let formattedParagraph = paragraph.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      
      // Handle bullet points (starting with * or -)
      if (formattedParagraph.trim().startsWith('*') || formattedParagraph.trim().startsWith('-')) {
        const bulletPoints = formattedParagraph.split('\n').filter(line => line.trim());
        const listItems = bulletPoints.map(point => {
          const cleanPoint = point.replace(/^[\*\-]\s*/, '');
          const formatted = cleanPoint.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
          return `<li>${formatted}</li>`;
        }).join('');
        
        return (
          <ul key={index} className="formatted-list" dangerouslySetInnerHTML={{ __html: listItems }} />
        );
      }
      
      // Handle headings (lines ending with colon and potentially bold)
      if (formattedParagraph.includes(':') && formattedParagraph.length < 100) {
        return (
          <h3 key={index} className="formatted-heading" dangerouslySetInnerHTML={{ __html: formattedParagraph }} />
        );
      }
      
      // Regular paragraph
      return (
        <p key={index} className="formatted-paragraph" dangerouslySetInnerHTML={{ __html: formattedParagraph }} />
      );
    });
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      {isSidebarVisible && (
        <div className="sidebar">
          <div className="sidebar-header">
            <h2 className="sidebar-title">Conversations</h2>
            <button className="new-chat-btn" onClick={startNewConversation}>New Chat</button>
          </div>
          
          {/* Connection Status */}
          <div className="connection-status">
            <div className={`status-indicator ${connectionStatus}`}>
              <span className={`status-dot ${connectionStatus}`}></span>
              <span className="status-text">
                {connectionStatus === 'connected' ? 'Connected' : 
                 connectionStatus === 'error' ? 'Connection Error' : 'Disconnected'}
              </span>
            </div>
            <button className="connection-toggle" onClick={toggleConnectionType}>
              {useWebSocket ? 'WebSocket' : 'REST API'}
            </button>
          </div>

          <div className="conversation-list">
            {conversationHistory.length === 0 ? (
              <p className="no-conversations">No conversation history yet</p>
            ) : conversationHistory.map(conv => (
              <div key={conv.id} className={`conversation-item ${selectedConversation?.id === conv.id ? "selected" : ""}`} onClick={() => loadConversation(conv)}>
                <div className="conversation-title">{conv.title}</div>
                <div className="conversation-timestamp">{conv.timestamp.toLocaleDateString()} {conv.timestamp.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="main-area">
        <div className="chat-header">
          <div className="header-left">
            <button className="sidebar-toggle-btn" onClick={toggleSidebar} aria-label={isSidebarVisible ? "Hide sidebar" : "Show sidebar"}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 12h18M3 6h18M3 18h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
            <h1 className="chat-title">HydroIntel Chatbot</h1>
          </div>
          <div className="header-actions">
            <div className="connection-info">
              <span className={`connection-badge ${connectionStatus}`}>
                {useWebSocket ? 'WebSocket' : 'REST'} • {connectionStatus}
              </span>
            </div>
            <button className="new-chat-btn" onClick={startNewConversation}>New Conversation</button>
          </div>
        </div>

        <div className="messages-container">
          <div className="messages-wrapper">
            {messages.map((msg, index) => (
              <div key={index} className={`message-row ${msg.sender}`}>
                <div className={`avatar ${msg.sender}`}>{msg.sender === "bot" ? "🌊" : "👤"}</div>
                <div className={`message-bubble ${msg.sender}`}>
                  <div className="message-text">
                    {msg.sender === "bot" ? (
                      <div className="formatted-message">
                        {formatText(msg.text)}
                      </div>
                    ) : (
                      msg.text
                    )}
                  </div>
                  <div className={`message-time ${msg.sender}`}>{msg.timestamp.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</div>
                </div>
              </div>
            ))}
            {isTyping && <div className="typing-indicator"><div className="typing-dot"></div><div className="typing-dot"></div><div className="typing-dot"></div></div>}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="input-area">
          <div className="input-wrapper">
            {recognition && (
              <button
                className={`voice-btn ${isListening ? "listening" : ""} mic-left`}
                onClick={toggleVoiceRecognition}
                aria-label={isListening ? "Stop voice input" : "Start voice input"}
                title={isListening ? "Stop" : "Voice"}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                  <path d="M12 14a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v5a3 3 0 0 0 3 3z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M19 11a7 7 0 0 1-14 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M12 19v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
            )}
            <input
              ref={inputRef}
              type="text"
              className={`message-input ${recognition ? 'with-mic' : ''}`}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about groundwater levels in Tamil or English..."
              onKeyDown={e => e.key === "Enter" && handleSend()}
            />
            <button className="send-btn" onClick={() => handleSend()} disabled={!input.trim()}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
                <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        {isListening && (
          <div className="listening-indicator">
            <span className="listening-badge"><span className="listening-pulse"></span>Listening...</span>
          </div>
        )}
      </div>
    </div>
  );
}
