export interface AgentHealth {
  siteId: string;
  lastHeartbeat: string;
  hasLastHeartbeat: boolean;
}

export enum AgentStatus {
  HEALTHY = 'HEALTHY',
  DEGRADED = 'DEGRADED',
  OFFLINE = 'OFFLINE',
  UNKNOWN = 'UNKNOWN'
}
