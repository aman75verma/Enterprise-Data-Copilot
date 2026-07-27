import { Bot, User } from 'lucide-react';
import { type Turn } from '../api/client';
import { ToolCallTrace } from './ToolCallTrace';

interface Props {
  turn: Turn;
  isDevMode: boolean;
}

export function MessageBubble({ turn, isDevMode }: Props) {
  const isUser = turn.role === 'user';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
      <div className={`message-wrapper ${isUser ? 'user' : 'ai'}`}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            marginBottom: 6,
            alignSelf: isUser ? 'flex-end' : 'flex-start',
            color: 'var(--text-muted)',
            fontSize: '0.75rem',
            fontWeight: 500,
          }}
        >
          {isUser ? (
            <>You <User size={12} /></>
          ) : (
            <><Bot size={12} /> Copilot</>
          )}
        </div>
        <div className="message-bubble">{turn.content}</div>
      </div>

      {isDevMode && turn.role === 'assistant' && turn.tool_calls && (
        <div style={{ marginTop: 12, marginBottom: 16 }}>
          <ToolCallTrace calls={turn.tool_calls} latency={turn.latency_ms} />
        </div>
      )}
    </div>
  );
}
