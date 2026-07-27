import { Terminal, Clock } from 'lucide-react';
import { type ToolCall } from '../api/client';

interface Props {
  calls: ToolCall[];
  latency?: number | null;
}

export function ToolCallTrace({ calls, latency }: Props) {
  if (!calls || calls.length === 0) return null;

  return (
    <>
      {calls.map((call, idx) => (
        <div key={idx} className="trace-panel">
          <div className="trace-header">
            <div className="trace-title">
              <Terminal size={12} /> Tool Execution
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span className="trace-badge">{call.tool}</span>
              {latency != null && (
                <span className="trace-latency">
                  <Clock size={10} style={{ display: 'inline', marginRight: 3, verticalAlign: 'text-bottom' }} />
                  {latency}ms
                </span>
              )}
            </div>
          </div>

          <div className="trace-section-label">Arguments</div>
          <div className="trace-code">
            {call.arguments.sql_query
              ? call.arguments.sql_query
              : JSON.stringify(call.arguments, null, 2)}
          </div>

          <div className="trace-section-label">Result</div>
          <div className="trace-code" style={{ maxHeight: 100, overflowY: 'auto' }}>
            {JSON.stringify(call.result, null, 2)}
          </div>
        </div>
      ))}
    </>
  );
}
