/**
 * @synapseos/types — Health API Types
 */

export interface HealthStatus {
  status: string;
  version?: string;
  environment?: string;
  check_duration_ms?: number;
  services: Record<string, ServiceHealth>;
}

export interface ServiceHealth {
  status: 'healthy' | 'unhealthy' | 'unavailable' | 'unknown';
  host?: string;
  port?: number;
  uri?: string;
  url?: string;
  error?: string;
}

export interface RootResponse {
  name: string;
  version: string;
  docs: string;
  status: string;
}
