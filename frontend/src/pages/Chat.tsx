import { useState, useRef, useEffect } from 'react';
import { Send, Database, FileText, Bug, Plus, Bot } from 'lucide-react';
import { api, type Turn } from '../api/client';
import { MessageBubble } from '../components/MessageBubble';
import { TopNav } from '../components/TopNav';

const SUGGESTIONS = [
  { icon: Database, text: 'How many customers are on the enterprise plan?', color: 'chip-db' },
  { icon: Database, text: 'Show open tickets related to Auth', color: 'chip-db' },
  { icon: FileText, text: 'How do I enable Row Level Security?', color: 'chip-doc' },
  { icon: Bug, text: 'Any open bugs related to Edge Functions?', color: 'chip-bug' },
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
      id: Date.now(), role: 'user', content: text.trim(),
      tool_calls: null, tool_name: null, latency_ms: null,
    };
    setMessages(prev => [...prev, optimistic]);

    try {
      const data = await api.chat(text.trim(), conversationId);
      if (!conversationId) setConversationId(data.conversation_id);
      const fullConv = await api.getConversation(data.conversation_id);
      setMessages(fullConv.turns);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: 'assistant',
        content: `Error: ${err.message || 'Could not reach the backend. Is uvicorn running on port 8000?'}`,
        tool_calls: null, tool_name: null, latency_ms: null,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => { e.preventDefault(); sendMessage(input); };
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input); }
  };
  const handleNewChat = () => { setMessages([]); setConversationId(undefined); setInput(''); };

  return (
    <>
      <div className="bg-glow" />
      <div className="app-shell">
        <TopNav isDevMode={isDevMode} setIsDevMode={setIsDevMode} />

        <div className="chat-layout glass">
          <div className="messages-scroll">
            {messages.length === 0 && (
              <div className="welcome">
                <div className="welcome-icon">
                  <Bot size={34} color="#080c14" strokeWidth={2} />
                </div>
                <h1>What can I help you with?</h1>
                <p>Query customer databases, search product documentation, or check live GitHub issues — all powered by AI.</p>

                <div className="welcome-grid">
                  {SUGGESTIONS.map((s, i) => (
                    <button key={i} className="welcome-chip" onClick={() => sendMessage(s.text)}>
                      <div className={`welcome-chip-icon ${s.color}`}>
                        <s.icon size={14} />
                      </div>
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
              <div className="typing-row">
                <div className="msg-avatar ai-av"><Bot size={14} /></div>
                <div className="typing-dots">
                  <span /><span /><span />
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <div className="input-row">
            {messages.length > 0 && (
              <button className="btn btn-sm" onClick={handleNewChat} title="Start new conversation">
                <Plus size={13} /> New
              </button>
            )}
            <form onSubmit={handleSubmit} className="input-box">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about customers, docs, or issues..."
                rows={1}
                disabled={isLoading}
              />
              <button type="submit" className="send-btn" disabled={!input.trim() || isLoading}>
                <Send size={15} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
