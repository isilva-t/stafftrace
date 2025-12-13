import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { EmployeeMonthlyDetail } from '../../models/employee.model';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-employee-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './employee-detail.html',
  styleUrl: './employee-detail.css'
})
export class EmployeeDetail implements OnInit {
  employeeId!: number;
  year!: number;
  month!: number;
  detail: EmployeeMonthlyDetail | null = null;
  loading = true;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService
  ) { }

  ngOnInit(): void {

    this.route.params.subscribe(params => {
      this.employeeId = +params['id'];
    });

    this.route.queryParams.subscribe(queryParams => {
      this.year = +queryParams['year'];
      this.month = +queryParams['month'];
      this.loadData();
    });
  }

  loadData(): void {
    this.loading = true;
    this.apiService.getEmployeeMonthlyDetail(this.employeeId, this.year, this.month).subscribe({
      next: (data) => {
        const firstActiveIndex = data.dailyRecords.findIndex(day => day.hours > 0);
        let lastActiveIndex = -1;
        for (let i = data.dailyRecords.length - 1; i >= 0; i--) {
          if (data.dailyRecords[i].hours > 0) {
            lastActiveIndex = i;
            break;
          }
        }

        if (firstActiveIndex !== -1 && lastActiveIndex !== -1) {
          data.dailyRecords = data.dailyRecords.slice(firstActiveIndex, lastActiveIndex);
        }

        this.detail = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Failed to load data';
        this.loading = false;
        console.error(err);
      }
    });
  }

  getMonthName(): string {
    if (!this.detail) return '';
    const date = new Date(this.detail.year, this.detail.month - 1);
    return date.toLocaleDateString(environment.locale, { month: 'long', year: 'numeric' });
  }

  goBack(): void {
    this.router.navigate(['/monthly'], {
      queryParams: { year: this.year, month: this.month }
    });
  }

  getStatusClass(status: string): string {
    switch (status) {
      case 'Full day': return 'status-full';
      case 'Partial': return 'status-partial';
      case 'Weekend': return 'status-weekend';
      case 'Absent': return 'status-absent';
      default: return '';
    }
  }

  formatTime(time: string | null): string {
    if (!time) return '-';
    // time comes as "10:54:55.075" or "10:54:55"
    // Extract just HH:MM
    const parts = time.split(':');
    if (parts.length >= 2) {
      return `${parts[0]}:${parts[1]}`;
    }
    return time;
  }
  formatDayHeader(date: string, dayOfWeek: string): string {
    // Extract day number from "2025-12-08" -> "08"
    const dayNumber = date.split('-')[2];
    const dayAbbrev = dayOfWeek.substring(0, 3);
    return `${dayNumber} ${dayAbbrev}`;
  }
}
