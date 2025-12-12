import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { EmployeeStatus } from '../../models/employee.model';
import { AgentDowntime } from '../../models/downtime.model';
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
  }

  refresh(): void {
    this.loading = true;
    this.loadData();
  }

  formatTime(isoString: string): string {
    return new Date(isoString).toLocaleTimeString(environment.locale, {
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  formatDowntime(downtime: AgentDowntime): string {
    const start = new Date(downtime.downtimeStart);
    const end = new Date(downtime.downtimeEnd);
    const startTime = start.toLocaleTimeString(environment.locale, { hour: '2-digit', minute: '2-digit' });
    const endTime = end.toLocaleTimeString(environment.locale, { hour: '2-digit', minute: '2-digit' });
    return `${startTime} - ${endTime}`;
  }
}
