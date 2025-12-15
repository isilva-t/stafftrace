import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { EmployeeStatus } from '../../models/employee.model';
import { AgentDowntime } from '../../models/downtime.model';
import { AgentHealth, AgentStatus } from '../../models/agent-health.model';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-current-status',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './current-status.html',
  styleUrl: './current-status.css',
})
export class CurrentStatus implements OnInit, OnDestroy {
  employees: EmployeeStatus[] = [];
  loading = true;
  error = '';
  lastUpdated = new Date();
  downtimes: AgentDowntime[] = [];
  agentHealthData: AgentHealth[] = []
  agentStatus: AgentStatus = AgentStatus.UNKNOWN;
  agentLastSeen: string = "";
  private refreshInterval: any;

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.loadData();
    this.refreshInterval = setInterval(() => {
      this.loadData();
    }, environment.refreshInterval);
  }

  ngOnDestroy(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  loadData(): void {
    const today = new Date().toISOString().split("T")[0];

    this.apiService.getCurrentStatus().subscribe({
      next: (data) => {
        this.employees = data;
        this.lastUpdated = new Date();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load data';
        this.loading = false;
        console.error(err);
      }
    });

    this.apiService.getDowntimes(today).subscribe({
      next: (data) => {
        this.downtimes = data;
      },
      error: (err) => {
        console.error('Failed to load downtimes:', err);
      }
    });

    this.apiService.getAgentHealth().subscribe({
      next: (data) => {
        this.agentHealthData = data;
        this.calculateAgentStatus();
      },
      error: (err) => {
        console.error('Failed to load agent health:', err);
        this.agentStatus = AgentStatus.UNKNOWN;
      }
    });
  }

  refresh(): void {
    this.loading = true;
    this.loadData();
  }

  formatTime(isoString: string): string {
    const date = new Date(isoString);
    const today = new Date();

    const isToday = date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear();

    if (isToday) {
      return `Today, ${new Date(isoString).toLocaleTimeString(environment.locale, {
        hour: '2-digit',
        minute: '2-digit'
      })}`;
    }
    return date.toLocaleDateString(environment.locale, {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  }

  formatDowntime(downtime: AgentDowntime): string {
    const start = new Date(downtime.downtimeStart);
    const end = new Date(downtime.downtimeEnd);
    const startTime = start.toLocaleTimeString(environment.locale, { hour: '2-digit', minute: '2-digit' });
    const endTime = end.toLocaleTimeString(environment.locale, { hour: '2-digit', minute: '2-digit' });
    return `${startTime} - ${endTime}`;
  }

  private calculateAgentStatus(): void {
    if (this.agentHealthData.length === 0) {
      this.agentStatus = AgentStatus.UNKNOWN;
      this.agentLastSeen = 'No agent data';
      return;
    }

    const agent = this.agentHealthData[0];

    if (!agent.hasLastHeartbeat || !agent.lastHeartbeat) {
      this.agentStatus = AgentStatus.UNKNOWN;
      this.agentLastSeen = 'No Heartbeat received';
      return;
    }

    const now = new Date();
    const lastHeartbeat = new Date(agent.lastHeartbeat);
    const secondsAgo = Math.floor((now.getTime() - lastHeartbeat.getTime()) / 1000)

    if (secondsAgo < environment.healthy) {
      this.agentStatus = AgentStatus.HEALTHY;
    } else if (secondsAgo <= environment.degraded) {
      this.agentStatus = AgentStatus.DEGRADED;
    } else {
      this.agentStatus = AgentStatus.OFFLINE;
    }

    this.agentLastSeen = `${secondsAgo} seconds ago`;
  }
}
