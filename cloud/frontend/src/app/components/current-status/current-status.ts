import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { EmployeeStatus } from '../../models/employee.model';
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
}
