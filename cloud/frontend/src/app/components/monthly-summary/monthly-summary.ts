import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { MonthlyPresence } from '../../models/employee.model';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'app-monthly-summary',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './monthly-summary.html',
  styleUrl: './monthly-summary.css'
})
export class MonthlySummary implements OnInit {
  selectedYear = new Date().getFullYear();
  selectedMonth = new Date().getMonth() + 1;
  records: MonthlyPresence[] = [];
  loading = true;
  error = '';

  constructor(private apiService: ApiService) { }

  ngOnInit(): void { this.loadData(); }

  loadData(): void {
    this.loading = true;
    this.apiService.getMonthlyReport(this.selectedYear, this.selectedMonth).subscribe({
      next: (data) => {
        this.records = data;
        this.loading = false
      },
      error: (err) => {
        this.error = 'Failed to load data';
        this.loading = false;
        console.error(err);
      }
    });
  }

  previousMonth(): void {
    if (this.selectedMonth === 1) {
      this.selectedMonth = 12;
      this.selectedYear--;
    } else { this.selectedMonth--; }
    this.loadData();
  }

  nextMonth(): void {
    if (this.selectedMonth === 12) {
      this.selectedMonth = 1;
      this.selectedYear++;
    } else { this.selectedMonth++ }
    this.loadData();
  }

  getMonthName(): string {
    const date = new Date(this.selectedYear, this.selectedMonth - 1);
    return date.toLocaleDateString(environment.locale, { month: 'long', year: 'numeric' });
  }
}
