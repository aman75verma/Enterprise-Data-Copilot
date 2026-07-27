import { useEffect, useState } from 'react';
import { Activity, Clock, Zap, AlertTriangle, Database, RefreshCw } from 'lucide-react';
import { api, type LogEntry, type CompareResponse } from '../api/client';
import { TopNav } from '../components/TopNav';

const TOOL_PRESETS: Record<string, string> = {
  query_customer_db: '{\n  "sql_query": "SELECT COUNT(*) FROM customers"\n}',
  search_docs: '{\n  "query": "Row Level Security",\n  "top_k": 3\n}',
  check_issue_tracker: '{\n  "keyword": "auth",\n  "issue_number": null\n}',
};

export function AdminDashboard() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [toolName, setToolName] = useState('query_customer_db');
  const [argsJson, setArgsJson] = useState(TOOL_PRESETS['query_customer_db']);
  const [isComparing, setIsComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [compareError, setCompareError] = useState<string | null>(null);

  useEffect(() => { fetchLogs(); }, []);

  const fetchLogs = async () => {
    try { setLogs(await api.getLogs(50)); } catch (err) { console.error(err); }
  };

  const handleToolChange = (name: string) => {
    setToolName(name);
    setArgsJson(TOOL_PRESETS[name] || '{}');
    setCompareResult(null);
    setCompareError(null);
  };

  const runComparison = async () => {
    try {
      setIsComparing(true);
      setCompareError(null);
      const parsed = JSON.parse(argsJson);
      setCompareResult(await api.compare(toolName, parsed));
    } catch (err: any) {
      setCompareError(err.message || 'Comparison failed');
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <>
      <div className="bg-glow" />
      <div className="admin-shell">
        <TopNav isDevMode={false} setIsDevMode={() => {}} />

        {/* ── Comparison ── */}
        <div className="admin-section glass">
          <h2>
            <Activity size={18} color="var(--accent)" />
            Dual-Path Latency Comparison
          </h2>
          <p className="subtitle">
            Execute a tool via the Orchestrator's direct Python path and compare latency against the MCP network path.
          </p>

          <div className="form-row">
            <div className="form-group flex-1">
              <label className="form-label">Tool</label>
              <select
                className="form-select"
                value={toolName}
                onChange={e => handleToolChange(e.target.value)}
              >
                <option value="query_customer_db">query_customer_db</option>
                <option value="search_docs">search_docs</option>
                <option value="check_issue_tracker">check_issue_tracker</option>
              </select>
            </div>
            <div className="form-group flex-2">
              <label className="form-label">Arguments (JSON)</label>
              <textarea
                className="form-textarea"
                value={argsJson}
                onChange={e => setArgsJson(e.target.value)}
              />
            </div>
          </div>

          <button className="btn btn-accent" onClick={runComparison} disabled={isComparing}>
            {isComparing ? (
              <><RefreshCw size={14} style={{ animation: 'spin 1s linear infinite' }} /> Running...</>
            ) : (
              <><Zap size={14} /> Run Benchmark</>
            )}
          </button>

          {compareError && (
            <div className="error-banner">
              <AlertTriangle size={14} /> {compareError}
            </div>
          )}

          {compareResult && (
            <div className="compare-results">
              <div className="compare-card" style={{ borderColor: 'rgba(62,207,142,0.15)' }}>
                <div className="compare-card-label" style={{ color: 'var(--accent)' }}>
                  <Zap size={13} /> Direct (Orchestrator)
                </div>
                <div className="compare-card-value">
                  {compareResult.direct_ms}<span className="compare-card-unit">ms</span>
                </div>
              </div>

              <div className="compare-card">
                <div className="compare-card-label" style={{ color: 'var(--text-muted)' }}>
                  <Clock size={13} /> MCP Network
                </div>
                {compareResult.mcp_ms != null ? (
                  <div className="compare-card-value">
                    {compareResult.mcp_ms}<span className="compare-card-unit">ms</span>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-faint)', fontStyle: 'italic', fontSize: '0.82rem', marginTop: 8 }}>
                    {compareResult.mcp_error}
                  </div>
                )}
              </div>

              <div className="compare-preview">
                <div className="compare-preview-label">Result Preview</div>
                <div className="trace-code">{compareResult.result_preview}</div>
              </div>
            </div>
          )}
        </div>

        {/* ── Logs ── */}
        <div className="admin-section glass">
          <h2>
            <Database size={18} color="var(--accent)" />
            Tool Execution Logs
          </h2>
          <p className="subtitle">All tool calls across conversations, ordered by most recent.</p>

          <table className="logs-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>Tool</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr><td colSpan={4} className="empty-state">No tool executions logged yet. Send a chat message first.</td></tr>
              ) : logs.map(log => (
                <tr key={log.id}>
                  <td className="mono">#{log.id}</td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--text-faint)' }}>{log.created_at}</td>
                  <td><span className="trace-badge">{log.tool_name}</span></td>
                  <td className={`mono ${(log.latency_ms || 0) < 500 ? 'latency-fast' : (log.latency_ms || 0) < 1500 ? 'latency-med' : 'latency-slow'}`}>
                    {log.latency_ms}ms
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
