/**
 * Shared constants.
 */

export const MEMORY_TYPES = ['episodic', 'semantic', 'procedural'] as const;

export const AGENT_TYPES = [
  'executive',
  'memory',
  'research',
  'planning',
  'communication',
  'coding',
  'reflection',
  'router',
] as const;

export const AGENT_STATUS = ['idle', 'busy', 'offline', 'error'] as const;

export const API_VERSION = 'v1';

export const MAX_MEMORY_CONTENT_LENGTH = 10000;
export const MAX_SEARCH_RESULTS = 100;
export const DEFAULT_PAGE_SIZE = 20;
