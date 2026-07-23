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
   * TODO: Implement
   */
  async health(): Promise<{ status: string }> {
    const response = await fetch(`${this.apiUrl}/health`);
    return response.json();
  }
}

// TODO: Export sub-modules
// export { MemoryClient } from './memory';
// export { AgentClient } from './agents';
// export { GraphClient } from './graph';
// export { RAGClient } from './rag';
