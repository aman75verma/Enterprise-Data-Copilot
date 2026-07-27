// API Client for the FastAPI Backend
const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export interface ToolCall {
  tool: string;
  arguments: any;
  result: any;
}

export interface Turn {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  tool_calls: ToolCall[] | null;
  tool_name: string | null;
  latency_ms: number | null;
}

export interface Conversation {
  conversation_id: string;
  created_at: string;
  turns: Turn[];
}

export interface LogEntry {
  id: number;
  conversation_id: string;
  created_at: string;
  role: string;
  content: string;
  tool_name: string | null;
  latency_ms: number | null;
}

export interface CompareResponse {
  tool_name: string;
  direct_ms: number;
  mcp_ms: number | null;
  mcp_error: string | null;
  result_preview: string;
}

export const api = {
  // Send a message and get a response
  chat: async (message: string, conversationId?: string) => {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_id: conversationId })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Fetch full history of a conversation
  getConversation: async (id: string): Promise<Conversation> => {
    const res = await fetch(`${BASE_URL}/conversations/${id}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Fetch recent tool executions for Admin Dashboard
  getLogs: async (limit: number = 50): Promise<LogEntry[]> => {
    const res = await fetch(`${BASE_URL}/admin/logs?limit=${limit}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Run the dual-path comparison tester
  compare: async (toolName: string, args: any): Promise<CompareResponse> => {
    const res = await fetch(`${BASE_URL}/admin/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool_name: toolName, arguments: args })
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }
};
