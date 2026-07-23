/**
 * Application-wide constants.
 */

export const APP_NAME = 'SynapseOS';
export const APP_DESCRIPTION = 'A Privacy-First AI Operating System';

export const API_ROUTES = {
  health: '/health',
  memory: '/api/v1/memory',
  agents: '/api/v1/agents',
  graph: '/api/v1/graph',
  rag: '/api/v1/rag',
  settings: '/api/v1/settings',
  auth: '/api/v1/auth',
} as const;

export const NAVIGATION = [
  { label: 'Dashboard', href: '/', icon: 'LayoutDashboard' },
  { label: 'Memory', href: '/memory', icon: 'Brain' },
  { label: 'Knowledge Graph', href: '/graph', icon: 'GitBranch' },
  { label: 'Agents', href: '/agents', icon: 'Bot' },
  { label: 'Settings', href: '/settings', icon: 'Settings' },
] as const;

export const MEMORY_TYPES = {
  EPISODIC: 'episodic',
  SEMANTIC: 'semantic',
  PROCEDURAL: 'procedural',
} as const;

export const AGENT_TYPES = {
  EXECUTIVE: 'executive',
  MEMORY: 'memory',
  RESEARCH: 'research',
  PLANNING: 'planning',
  COMMUNICATION: 'communication',
  CODING: 'coding',
  REFLECTION: 'reflection',
  ROUTER: 'router',
} as const;
