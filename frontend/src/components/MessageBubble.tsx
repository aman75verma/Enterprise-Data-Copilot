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
    <>
      <div className={`msg-row ${isUser ? 'user' : 'ai'}`}>
        <div className={`msg-avatar ${isUser ? 'user-av' : 'ai-av'}`}>
          {isUser ? <User size={14} /> : <Bot size={14} />}
        </div>
        <div className="msg-body">
          <span className="msg-label">{isUser ? 'You' : 'Copilot'}</span>
          <div className="msg-bubble">{turn.content}</div>
        </div>
      </div>

      {isDevMode && turn.role === 'assistant' && turn.tool_calls && turn.tool_calls.length > 0 && (
        <div style={{ maxWidth: '85%', alignSelf: 'flex-start', marginLeft: 42 }}>
          <ToolCallTrace calls={turn.tool_calls} latency={turn.latency_ms} />
        </div>
      )}
    </>
  );
}
