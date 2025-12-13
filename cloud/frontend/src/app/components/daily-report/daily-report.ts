import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { DailyPresence } from '../../models/employee.model';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-daily-report',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './daily-report.html',
  styleUrl: './daily-report.css'
})
export class DailyReport implements OnInit {
  selectedDate = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  records: DailyPresence[] = [];
  loading = true;
  error = '';

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    this.apiService.getDailyReport(this.selectedDate).subscribe({
      next: (data) => {
        this.records = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load data';
        this.loading = false;
        console.error(err);
      }
    });
  }

  previousDay(): void {
    const date = new Date(this.selectedDate);
    date.setDate(date.getDate() - 1);
    this.selectedDate = date.toISOString().split('T')[0];
    this.loadData();
  }

  nextDay(): void {
    const date = new Date(this.selectedDate);
    date.setDate(date.getDate() + 1);
    this.selectedDate = date.toISOString().split('T')[0];
    this.loadData();
  }

  today(): void {
    this.selectedDate = new Date().toISOString().split('T')[0];
    this.loadData();
  }

  getStatus(hours: number): string {
    if (hours === 0) return 'Absent';
    if (hours >= 8) return 'Full day';
    return 'Partial';
  }

  formatTime(timeStr: string | null): string {
    if (!timeStr) return '-';
    return timeStr.substring(0, 5); // HH:MM:SS -> HH:MM
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString(environment.locale, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }
}
