import { useState, useRef, useEffect } from 'react';
import { Send, Loader, Database, FileText, Bug, Plus } from 'lucide-react';
import { api, type Turn } from '../api/client';
import { MessageBubble } from '../components/MessageBubble';
import { TopNav } from '../components/TopNav';

const SUGGESTIONS = [
  { icon: Database, text: 'How many customers are on the enterprise plan?' },
  { icon: Database, text: 'Show me open tickets for Auth issues' },
  { icon: FileText, text: 'How do I enable Row Level Security?' },
  { icon: Bug, text: 'Are there any open bugs related to Edge Functions?' },
];

export function Chat() {
  const [isDevMode, setIsDevMode] = useState(false);
  const [messages, setMessages] = useState<Turn[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;
    setInput('');
    setIsLoading(true);

    const optimistic: Turn = {
      id: Date.now(),
      role: 'user',
      content: text.trim(),
      tool_calls: null,
      tool_name: null,
      latency_ms: null,
    };
    setMessages((prev) => [...prev, optimistic]);

    try {
      const data = await api.chat(text.trim(), conversationId);
      if (!conversationId) setConversationId(data.conversation_id);
      const fullConv = await api.getConversation(data.conversation_id);
      setMessages(fullConv.turns);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: 'assistant',
          content: `❌ ${err.message || 'Failed to connect to backend.'}`,
          tool_calls: null,
          tool_name: null,
          latency_ms: null,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(undefined);
    setInput('');
  };

  return (
    <div className="app-container">
      <TopNav isDevMode={isDevMode} setIsDevMode={setIsDevMode} />

      <div className="main-content">
        <div className="chat-area glass-panel">
          <div className="messages-container">
            {messages.length === 0 && (
              <div className="welcome-screen">
                <div className="welcome-logo">
                  <Database size={32} color="#0b0f19" />
                </div>
                <h1>How can I help?</h1>
                <p>
                  Query customer data, search product docs, or check live GitHub issues — all in one place.
                </p>
                <div className="suggested-questions">
                  {SUGGESTIONS.map((s, i) => (
                    <button
                      key={i}
                      className="suggestion-chip"
                      onClick={() => sendMessage(s.text)}
                    >
                      <span className="suggestion-icon">
                        <s.icon size={14} />
                      </span>
                      {s.text}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((turn, idx) => (
              <MessageBubble key={turn.id || idx} turn={turn} isDevMode={isDevMode} />
            ))}

            {isLoading && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                <Loader size={14} style={{ animation: 'spin 1.5s linear infinite' }} />
                Thinking...
              </div>
            )}
            <div ref={endRef} />
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {messages.length > 0 && (
              <button className="glass-button new-chat-btn" onClick={handleNewChat}>
                <Plus size={14} /> New
              </button>
            )}
            <form onSubmit={handleSubmit} className="input-area" style={{ flex: 1 }}>
              <textarea
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about customers, docs, or issues..."
                rows={1}
                disabled={isLoading}
              />
              <button
                type="submit"
                className="glass-button primary"
                disabled={!input.trim() || isLoading}
                style={{ padding: '10px 12px' }}
              >
                <Send size={16} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
