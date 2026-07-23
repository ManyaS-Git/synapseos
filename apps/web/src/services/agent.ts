/* ── Agent Service (stub) ──────────────────────────────────────────── */

// TODO: Implement agent service when agent-runtime is built

export const agentService = {
  async sendMessage(agentId: string, message: string) {
    // eslint-disable-next-line no-unused-vars
    void agentId; void message;
    throw new Error("Agent service not yet implemented");
  },

  async getStatus(agentId: string) {
    // eslint-disable-next-line no-unused-vars
    void agentId;
    throw new Error("Agent service not yet implemented");
  },

  async list() {
    throw new Error("Agent service not yet implemented");
  },
};
