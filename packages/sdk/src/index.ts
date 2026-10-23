/**
 * @synapseos/sdk — JavaScript/TypeScript SDK
 *
 * Programmatic access to SynapseOS capabilities.
 *
 * TODO: Implement the following:
 * - SynapseOS client class
 * - Memory module
 * - Agent module
 * - Graph module
 * - RAG module
 */

export class SynapseOS {
  private apiUrl: string;
  private apiKey?: string;

  constructor(options: { apiUrl: string; apiKey?: string }) {
    this.apiUrl = options.apiUrl;
    this.apiKey = options.apiKey;
  }

  /**
   * Check API health.
   */
  async health(): Promise<{ status: string }> {
    const headers: Record<string, string> = {};
    if (this.apiKey) {
      headers["Authorization"] = `Bearer ${this.apiKey}`;
    }
    const response = await fetch(`${this.apiUrl}/health`, { headers });
    return response.json();
  }
}

// TODO: Export sub-modules
// export { MemoryClient } from './memory';
// export { AgentClient } from './agents';
// export { GraphClient } from './graph';
// export { RAGClient } from './rag';
