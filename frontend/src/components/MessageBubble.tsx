import React from 'react';
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, alignSelf: isUser ? 'flex-end' : 'flex-start', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
          {isUser ? (
            <>You <User size={14} /></>
          ) : (
            <><Bot size={14} /> Support Copilot</>
          )}
        </div>
        
        <div className="message-bubble">
          {turn.content}
        </div>
      </div>
      
      {/* Dev Mode - Show Tool Trace if AI used tools */}
      {isDevMode && turn.role === 'assistant' && turn.tool_calls && (
        <div style={{ marginTop: 16, marginBottom: 24 }}>
          <ToolCallTrace calls={turn.tool_calls} latency={turn.latency_ms} />
        </div>
      )}
    </div>
  );
}
