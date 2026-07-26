import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader } from 'lucide-react';
import { api, type Turn } from '../api/client';
import { MessageBubble } from '../components/MessageBubble';
import { TopNav } from '../components/TopNav';

export function Chat() {
  const [isDevMode, setIsDevMode] = useState(false);
  const [messages, setMessages] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  
  const endRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    // Optimistically add user message to UI
    const optimisticTurn: Turn = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      tool_calls: null,
      tool_name: null,
      latency_ms: null
    };
    
    setMessages(prev => [...prev, optimisticTurn]);

    try {
      const data = await api.chat(userMessage, conversationId);
      
      // If it's a new conversation, save the ID
      if (!conversationId) {
        setConversationId(data.conversation_id);
      }

      // Fetch the updated full conversation to ensure we have the DB IDs and exact tool trace
      const fullConv = await api.getConversation(data.conversation_id);
      setMessages(fullConv.turns);
    } catch (err: any) {
      console.error(err);
      // Basic error handling for UI
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: `❌ Error: ${err.message || 'Failed to connect to backend.'}`,
        tool_calls: null,
        tool_name: null,
        latency_ms: null
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="app-container">
      <TopNav isDevMode={isDevMode} setIsDevMode={setIsDevMode} />
      
      <div className="main-content">
        <div className="chat-area glass-panel">
          <div className="messages-container">
            {messages.length === 0 && (
              <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <h2>Welcome to Enterprise Data Copilot</h2>
                <p style={{ marginTop: 8 }}>Ask about customers, tickets, or technical issues.</p>
              </div>
            )}
            
            {messages.map((turn, idx) => (
              <MessageBubble key={turn.id || idx} turn={turn} isDevMode={isDevMode} />
            ))}
            
            {isLoading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)' }}>
                <Loader size={16} className="animate-spin" style={{ animation: 'spin 2s linear infinite' }} />
                <span>Copilot is thinking...</span>
                <style>{`
                  @keyframes spin { 100% { transform: rotate(360deg); } }
                `}</style>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <form onSubmit={handleSubmit} className="input-area">
            <textarea
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question... (Press Enter to send)"
              rows={1}
              disabled={isLoading}
            />
            <button 
              type="submit" 
              className="glass-button primary" 
              disabled={!input.trim() || isLoading}
              style={{ padding: '10px 14px' }}
            >
              <Send size={18} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
