import React, { useEffect, useState } from 'react';
import { Activity, Clock, Zap, AlertTriangle, Database } from 'lucide-react';
import { api, type LogEntry, type CompareResponse } from '../api/client';
import { TopNav } from '../components/TopNav';

export function AdminDashboard() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  
  // Comparison State
  const [toolName, setToolName] = useState('query_customer_db');
  const [argsJson, setArgsJson] = useState('{\n  "sql_query": "SELECT COUNT(*) FROM customers"\n}');
  const [isComparing, setIsComparing] = useState(false);
  const [compareResult, setCompareResult] = useState<CompareResponse | null>(null);
  const [compareError, setCompareError] = useState<string | null>(null);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const data = await api.getLogs(50);
      setLogs(data);
    } catch (err) {
      console.error("Failed to fetch logs", err);
    }
  };

  const runComparison = async () => {
    try {
      setIsComparing(true);
      setCompareError(null);
      
      let parsedArgs = {};
      try {
        parsedArgs = JSON.parse(argsJson);
      } catch(e) {
        throw new Error("Invalid JSON in arguments field.");
      }

      const result = await api.compare(toolName, parsedArgs);
      setCompareResult(result);
      
    } catch (err: any) {
      setCompareError(err.message || 'Comparison failed');
    } finally {
      setIsComparing(false);
    }
  };

  return (
    <div className="app-container" style={{ maxWidth: 1000 }}>
      <TopNav isDevMode={false} setIsDevMode={() => {}} />
      
      <div className="main-content" style={{ flexDirection: 'column' }}>
        
        {/* Comparison Tester */}
        <div className="glass-panel" style={{ padding: 24 }}>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Activity size={20} color="var(--accent-color)" /> 
            Dual-Path Latency Comparison
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 24, fontSize: '0.9rem' }}>
            Run a tool through the Orchestrator's Direct Python execution path vs the simulated MCP Network execution path to measure latency differences.
          </p>

          <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: 8, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Tool Name</label>
              <select 
                className="chat-input" 
                style={{ width: '100%', background: 'rgba(0,0,0,0.2)' }}
                value={toolName}
                onChange={(e) => setToolName(e.target.value)}
              >
                <option value="query_customer_db">query_customer_db</option>
                <option value="search_docs">search_docs</option>
                <option value="check_issue_tracker">check_issue_tracker</option>
              </select>
            </div>
            <div style={{ flex: 2 }}>
              <label style={{ display: 'block', marginBottom: 8, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Arguments (JSON)</label>
              <textarea 
                className="chat-input code-block" 
                style={{ width: '100%', minHeight: 80 }}
                value={argsJson}
                onChange={(e) => setArgsJson(e.target.value)}
              />
            </div>
          </div>

          <button 
            className="glass-button primary" 
            onClick={runComparison} 
            disabled={isComparing}
          >
            {isComparing ? 'Running Benchmark...' : 'Run Benchmark'}
          </button>

          {compareError && (
            <div style={{ marginTop: 16, color: '#f85149', padding: 12, background: 'rgba(248, 81, 73, 0.1)', borderRadius: 8 }}>
              <AlertTriangle size={16} style={{display:'inline', marginRight:8}}/> 
              {compareError}
            </div>
          )}

          {compareResult && (
            <div className="compare-grid">
              <div className="compare-card glass-panel" style={{ background: 'rgba(63, 207, 142, 0.05)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent-color)' }}>
                  <Zap size={18} /> Path A: Direct Execution
                </div>
                <div className="metric-big">
                  {compareResult.direct_ms} <span style={{fontSize:'1rem', color:'var(--text-secondary)'}}>ms</span>
                </div>
              </div>
              
              <div className="compare-card glass-panel" style={{ background: 'rgba(255, 255, 255, 0.02)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Clock size={18} /> Path B: MCP Network
                </div>
                {compareResult.mcp_ms !== null ? (
                  <div className="metric-big">
                    {compareResult.mcp_ms} <span style={{fontSize:'1rem', color:'var(--text-secondary)'}}>ms</span>
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic', marginTop: 12 }}>
                    {compareResult.mcp_error}
                  </div>
                )}
              </div>
              
              <div style={{ gridColumn: '1 / -1', marginTop: 8 }}>
                <div className="metric-label">Result Preview</div>
                <div className="code-block" style={{ marginTop: 8 }}>{compareResult.result_preview}</div>
              </div>
            </div>
          )}
        </div>

        {/* Global Tool Logs */}
        <div className="glass-panel" style={{ padding: 24, marginTop: 24 }}>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Database size={20} color="var(--accent-color)" /> 
            Global Tool Execution Logs
          </h2>
          
          <div style={{ overflowX: 'auto' }}>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Turn ID</th>
                  <th>Timestamp</th>
                  <th>Tool Used</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: 24 }}>
                      No tool executions logged yet.
                    </td>
                  </tr>
                ) : (
                  logs.map(log => (
                    <tr key={log.id}>
                      <td style={{ fontFamily: 'monospace' }}>#{log.id}</td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{log.created_at}</td>
                      <td>
                        <span className="tool-badge">{log.tool_name}</span>
                      </td>
                      <td>
                        <span className={
                          (log.latency_ms || 0) < 500 ? 'latency-fast' : 
                          (log.latency_ms || 0) < 1500 ? 'latency-med' : 'latency-slow'
                        }>
                          {log.latency_ms} ms
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
