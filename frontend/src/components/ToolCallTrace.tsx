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
      <h2><Terminal size={16} /> Tool Execution Trace</h2>

      {calls.map((call, idx) => (
        <div key={idx} className="tool-trace glass-panel">
          <div className="tool-header">
            <span className="tool-badge">
              <Box size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'text-bottom' }} />
              {call.tool}
            </span>
            {latency && (
              <span className="latency-badge" title="Execution latency">
                <Clock size={11} style={{ display: 'inline', marginRight: 3, verticalAlign: 'text-bottom' }} />
                {latency}ms
              </span>
            )}
          </div>

          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Arguments
            </div>
            <div className="code-block">
              {call.arguments.sql_query
                ? call.arguments.sql_query
                : JSON.stringify(call.arguments, null, 2)}
            </div>
          </div>

          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.68rem', marginBottom: 4, marginTop: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Result
            </div>
            <div className="code-block" style={{ maxHeight: 120, overflow: 'auto' }}>
              {JSON.stringify(call.result, null, 2)}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
