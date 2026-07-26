import React from 'react';
import { Terminal, Clock, Box } from 'lucide-react';
import { type ToolCall } from '../api/client';

interface Props {
  calls: ToolCall[];
  latency?: number | null;
}

export function ToolCallTrace({ calls, latency }: Props) {
  if (!calls || calls.length === 0) return null;

  return (
    <div className="dev-panel">
      <h2><Terminal size={20} /> Developer Trace</h2>
      
      {calls.map((call, idx) => (
        <div key={idx} className="tool-trace glass-panel">
          <div className="tool-header">
            <span className="tool-badge"><Box size={14} style={{display: 'inline', marginRight: 4, verticalAlign: 'text-bottom'}} /> {call.tool}</span>
            {latency && (
              <span className="latency-badge" title="Database/API Latency">
                <Clock size={12} style={{display: 'inline', marginRight: 4, verticalAlign: 'text-bottom'}} /> 
                {latency}ms
              </span>
            )}
          </div>
          
          <div className="tool-args">
            <div style={{color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: 4}}>ARGUMENTS</div>
            <div className="code-block">
              {call.arguments.sql_query 
                ? call.arguments.sql_query 
                : JSON.stringify(call.arguments, null, 2)}
            </div>
          </div>
          
          <div className="tool-result">
            <div style={{color: 'var(--text-secondary)', fontSize: '0.75rem', marginBottom: 4, marginTop: 8}}>RESULT PREVIEW</div>
            <div className="code-block" style={{maxHeight: 120}}>
              {JSON.stringify(call.result, null, 2)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
