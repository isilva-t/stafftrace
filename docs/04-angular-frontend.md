# Angular Frontend - Technical Specification

## Overview

The Angular frontend provides a simple, functional dashboard for viewing employee presence data with:
- Public demo mode (fake names)
- Authenticated mode (real names)
- 4 main views: Current Status, Daily Report, Monthly Summary, Employee Detail
- JWT-based authentication

**Design Philosophy**: Brutally simple. No fancy animations, no complex styling. Function over form.

---

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── components/
│   │   │   ├── current-status/
│   │   │   │   ├── current-status.component.ts
│   │   │   │   ├── current-status.component.html
│   │   │   │   └── current-status.component.css
│   │   │   ├── daily-report/
│   │   │   │   ├── daily-report.component.ts
│   │   │   │   ├── daily-report.component.html
│   │   │   │   └── daily-report.component.css
│   │   │   ├── monthly-summary/
│   │   │   │   ├── monthly-summary.component.ts
│   │   │   │   ├── monthly-summary.component.html
│   │   │   │   └── monthly-summary.component.css
│   │   │   ├── employee-detail/
│   │   │   │   ├── employee-detail.component.ts
│   │   │   │   ├── employee-detail.component.html
│   │   │   │   └── employee-detail.component.css
│   │   │   └── login-modal/
│   │   │       ├── login-modal.component.ts
│   │   │       ├── login-modal.component.html
│   │   │       └── login-modal.component.css
│   │   ├── services/
│   │   │   ├── api.service.ts          # HTTP calls to backend
│   │   │   └── auth.service.ts         # JWT token management
│   │   ├── models/
│   │   │   └── employee.model.ts       # TypeScript interfaces
│   │   ├── app.component.ts
│   │   ├── app.component.html
│   │   ├── app.component.css
│   │   └── app.routes.ts               # Routing configuration
│   ├── styles.css                      # Global styles
│   └── index.html
├── angular.json
├── package.json
├── tsconfig.json
└── Dockerfile
```

---

## Models (TypeScript Interfaces)

```typescript
// src/app/models/employee.model.ts

export interface EmployeeStatus {
  employeeId: number;
  employeeName: string;
  isPresent: boolean;
  currentArea: string;
  lastSeen: string;  // ISO datetime string
}

export interface DailyPresence {
  employeeId: number;
  employeeName: string;
  date: string;
  firstSeen: string | null;  // HH:mm:ss
  lastSeen: string | null;
  totalMinutes: number;
  hoursPresent: number;
}

export interface MonthlyPresence {
  employeeId: number;
  employeeName: string;
  totalHours: number;
  daysPresent: number;
  avgHoursPerDay: number;
}

export interface DailyDetail {
  date: string;
  dayOfWeek: string;
  firstSeen: string | null;
  lastSeen: string | null;
  hours: number;
  status: string;  // 'Full day', 'Partial', 'Absent', 'Weekend'
}

export interface EmployeeMonthlyDetail {
  employeeId: number;
  employeeName: string;
  year: number;
  month: number;
  dailyRecords: DailyDetail[];
  totalHours: number;
  daysPresent: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  message: string;
}
```

---

## Services

### AuthService
```typescript
// src/app/services/auth.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { LoginRequest, LoginResponse } from '../models/employee.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8080/api/auth';
  private tokenKey = 'auth_token';

  constructor(private http: HttpClient) {}

  login(username: string, password: string): Observable<LoginResponse> {
    const request: LoginRequest = { username, password };
    return this.http.post<LoginResponse>(`${this.apiUrl}/login`, request)
      .pipe(
        tap(response => {
          localStorage.setItem(this.tokenKey, response.token);
        })
      );
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }
}
```

### ApiService
```typescript
// src/app/services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { 
  EmployeeStatus, 
  DailyPresence, 
  MonthlyPresence,
  EmployeeMonthlyDetail 
} from '../models/employee.model';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8080/api';

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  private getHeaders(): HttpHeaders {
    const token = this.authService.getToken();
    if (token) {
      return new HttpHeaders({
        'Authorization': `Bearer ${token}`
      });
    }
    return new HttpHeaders();
  }

  getCurrentStatus(): Observable<EmployeeStatus[]> {
    return this.http.get<EmployeeStatus[]>(
      `${this.apiUrl}/current`,
      { headers: this.getHeaders() }
    );
  }

  getDailyReport(date: string): Observable<DailyPresence[]> {
    return this.http.get<DailyPresence[]>(
      `${this.apiUrl}/daily?date=${date}`,
      { headers: this.getHeaders() }
    );
  }

  getMonthlyReport(year: number, month: number): Observable<MonthlyPresence[]> {
    return this.http.get<MonthlyPresence[]>(
      `${this.apiUrl}/monthly?year=${year}&month=${month}`,
      { headers: this.getHeaders() }
    );
  }

  getEmployeeMonthlyDetail(
    employeeId: number, 
    year: number, 
    month: number
  ): Observable<EmployeeMonthlyDetail> {
    return this.http.get<EmployeeMonthlyDetail>(
      `${this.apiUrl}/employee/${employeeId}/monthly?year=${year}&month=${month}`,
      { headers: this.getHeaders() }
    );
  }
}
```

---

## Components

### App Component (Root)
```typescript
// src/app/app.component.ts
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  constructor(public authService: AuthService) {}

  logout(): void {
    this.authService.logout();
    window.location.reload();
  }
}
```

```html
<!-- src/app/app.component.html -->
<div class="container">
  <header>
    <h1>{{ authService.isAuthenticated() ? 'PORTO OFFICE' : 'DEMO OFFICE' }} - PRESENCE MONITOR</h1>
    <div class="auth-info">
      <span *ngIf="!authService.isAuthenticated()">ℹ️ Viewing anonymized demo data</span>
      <span *ngIf="authService.isAuthenticated()">✓ Viewing real employee data</span>
      <button *ngIf="!authService.isAuthenticated()" routerLink="/login">Login</button>
      <button *ngIf="authService.isAuthenticated()" (click)="logout()">Logout</button>
    </div>
  </header>

  <nav>
    <a routerLink="/current" routerLinkActive="active">Current Status</a>
    <a routerLink="/daily" routerLinkActive="active">Daily Report</a>
    <a routerLink="/monthly" routerLinkActive="active">Monthly Summary</a>
  </nav>

  <main>
    <router-outlet></router-outlet>
  </main>
</div>
```

### Current Status Component
```typescript
// src/app/components/current-status/current-status.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { EmployeeStatus } from '../../models/employee.model';

@Component({
  selector: 'app-current-status',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './current-status.component.html',
  styleUrl: './current-status.component.css'
})
export class CurrentStatusComponent implements OnInit, OnDestroy {
  employees: EmployeeStatus[] = [];
  loading = true;
  error = '';
  lastUpdated = new Date();
  private refreshInterval: any;

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadData();
    // Auto-refresh every 60 seconds
    this.refreshInterval = setInterval(() => {
      this.loadData();
    }, 60000);
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

  getHoursToday(lastSeen: string): number {
    const now = new Date();
    const seen = new Date(lastSeen);
    const diffMs = now.getTime() - seen.getTime();
    return Math.max(0, diffMs / (1000 * 60 * 60));
  }

  formatTime(isoString: string): string {
    return new Date(isoString).toLocaleTimeString('en-GB', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  }
}
```

```html
<!-- src/app/components/current-status/current-status.component.html -->
<div class="view-header">
  <h2>Current Status</h2>
  <div class="view-actions">
    <span class="timestamp">{{ lastUpdated | date:'short' }}</span>
    <button (click)="refresh()" [disabled]="loading">Refresh ↻</button>
  </div>
</div>

<div *ngIf="loading" class="loading">Loading...</div>
<div *ngIf="error" class="error">{{ error }}</div>

<div *ngIf="!loading && !error" class="employee-grid">
  <div *ngFor="let emp of employees" class="employee-card">
    <div class="employee-header">
      <span [class]="emp.isPresent ? 'status-online' : 'status-offline'">
        {{ emp.isPresent ? '●' : '○' }}
      </span>
      <h3>{{ emp.employeeName }}</h3>
    </div>
    <div class="employee-details">
      <p *ngIf="emp.isPresent">
        Present since {{ formatTime(emp.lastSeen) }}
      </p>
      <p *ngIf="!emp.isPresent">
        Last seen {{ formatTime(emp.lastSeen) }}
      </p>
      <p class="area">Area: {{ emp.currentArea }}</p>
    </div>
  </div>
</div>
```

### Daily Report Component
```typescript
// src/app/components/daily-report/daily-report.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { DailyPresence } from '../../models/employee.model';

@Component({
  selector: 'app-daily-report',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './daily-report.component.html',
  styleUrl: './daily-report.component.css'
})
export class DailyReportComponent implements OnInit {
  selectedDate = new Date().toISOString().split('T')[0];
  records: DailyPresence[] = [];
  loading = true;
  error = '';

  constructor(private apiService: ApiService) {}

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
}
```

```html
<!-- src/app/components/daily-report/daily-report.component.html -->
<div class="view-header">
  <h2>Daily Report</h2>
  <div class="date-controls">
    <button (click)="previousDay()">◀</button>
    <input type="date" [(ngModel)]="selectedDate" (change)="loadData()" />
    <button (click)="nextDay()">▶</button>
    <button (click)="today()">Today</button>
  </div>
</div>

<div *ngIf="loading" class="loading">Loading...</div>
<div *ngIf="error" class="error">{{ error }}</div>

<table *ngIf="!loading && !error" class="data-table">
  <thead>
    <tr>
      <th>Employee</th>
      <th>Arrived</th>
      <th>Left</th>
      <th>Hours</th>
      <th>Status</th>
    </tr>
  </thead>
  <tbody>
    <tr *ngFor="let record of records">
      <td>{{ record.employeeName }}</td>
      <td>{{ record.firstSeen || '-' }}</td>
      <td>{{ record.lastSeen || '-' }}</td>
      <td>{{ record.hoursPresent.toFixed(1) }}h</td>
      <td>{{ getStatus(record.hoursPresent) }}</td>
    </tr>
  </tbody>
</table>

<div class="schedule-info">
  <p><strong>Working schedule:</strong></p>
  <p>Monday-Friday: 08:30-12:30, 14:00-18:30</p>
  <p>Saturday: 08:30-12:30</p>
</div>
```

### Monthly Summary Component
```typescript
// src/app/components/monthly-summary/monthly-summary.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../services/api.service';
import { MonthlyPresence } from '../../models/employee.model';

@Component({
  selector: 'app-monthly-summary',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './monthly-summary.component.html',
  styleUrl: './monthly-summary.component.css'
})
export class MonthlySummaryComponent implements OnInit {
  selectedYear = new Date().getFullYear();
  selectedMonth = new Date().getMonth() + 1;
  records: MonthlyPresence[] = [];
  loading = true;
  error = '';

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading = true;
    this.apiService.getMonthlyReport(this.selectedYear, this.selectedMonth).subscribe({
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

  previousMonth(): void {
    if (this.selectedMonth === 1) {
      this.selectedMonth = 12;
      this.selectedYear--;
    } else {
      this.selectedMonth--;
    }
    this.loadData();
  }

  nextMonth(): void {
    if (this.selectedMonth === 12) {
      this.selectedMonth = 1;
      this.selectedYear++;
    } else {
      this.selectedMonth++;
    }
    this.loadData();
  }

  getMonthName(): string {
    const date = new Date(this.selectedYear, this.selectedMonth - 1);
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  }
}
```

```html
<!-- src/app/components/monthly-summary/monthly-summary.component.html -->
<div class="view-header">
  <h2>Monthly Report</h2>
  <div class="month-controls">
    <button (click)="previousMonth()">◀</button>
    <span class="month-display">{{ getMonthName() }}</span>
    <button (click)="nextMonth()">▶</button>
  </div>
</div>

<div *ngIf="loading" class="loading">Loading...</div>
<div *ngIf="error" class="error">{{ error }}</div>

<table *ngIf="!loading && !error" class="data-table">
  <thead>
    <tr>
      <th>Employee</th>
      <th>Total Hours</th>
      <th>Days Present</th>
      <th>Avg/Day</th>
    </tr>
  </thead>
  <tbody>
    <tr *ngFor="let record of records">
      <td>
        <a [routerLink]="['/employee', record.employeeId]" 
           [queryParams]="{year: selectedYear, month: selectedMonth}">
          {{ record.employeeName }}
        </a>
      </td>
      <td>{{ record.totalHours.toFixed(1) }}h</td>
      <td>{{ record.daysPresent }} days</td>
      <td>{{ record.avgHoursPerDay.toFixed(1) }}h</td>
    </tr>
  </tbody>
</table>
```

### Login Modal Component
```typescript
// src/app/components/login-modal/login-modal.component.ts
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login-modal.component.html',
  styleUrl: './login-modal.component.css'
})
export class LoginModalComponent {
  username = '';
  password = '';
  error = '';
  loading = false;

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  login(): void {
    this.loading = true;
    this.error = '';

    this.authService.login(this.username, this.password).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/current']);
        window.location.reload();
      },
      error: (err) => {
        this.error = 'Invalid credentials';
        this.loading = false;
        console.error(err);
      }
    });
  }

  cancel(): void {
    this.router.navigate(['/current']);
  }
}
```

```html
<!-- src/app/components/login-modal/login-modal.component.html -->
<div class="modal-overlay">
  <div class="modal-content">
    <h2>🔐 Admin Login</h2>
    
    <form (ngSubmit)="login()">
      <div class="form-group">
        <label>Username:</label>
        <input 
          type="text" 
          [(ngModel)]="username" 
          name="username"
          required 
          autofocus
        />
      </div>

      <div class="form-group">
        <label>Password:</label>
        <input 
          type="password" 
          [(ngModel)]="password" 
          name="password"
          required
        />
      </div>

      <div *ngIf="error" class="error">{{ error }}</div>

      <div class="form-actions">
        <button type="submit" [disabled]="loading || !username || !password">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
        <button type="button" (click)="cancel()">Cancel</button>
      </div>
    </form>
  </div>
</div>
```

---

## Routing

```typescript
// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { CurrentStatusComponent } from './components/current-status/current-status.component';
import { DailyReportComponent } from './components/daily-report/daily-report.component';
import { MonthlySummaryComponent } from './components/monthly-summary/monthly-summary.component';
import { EmployeeDetailComponent } from './components/employee-detail/employee-detail.component';
import { LoginModalComponent } from './components/login-modal/login-modal.component';

export const routes: Routes = [
  { path: '', redirectTo: '/current', pathMatch: 'full' },
  { path: 'current', component: CurrentStatusComponent },
  { path: 'daily', component: DailyReportComponent },
  { path: 'monthly', component: MonthlySummaryComponent },
  { path: 'employee/:id', component: EmployeeDetailComponent },
  { path: 'login', component: LoginModalComponent }
];
```

---

## Global Styles

```css
/* src/styles.css */
:root {
  --color-online: #22c55e;
  --color-offline: #6b7280;
  --color-background: #ffffff;
  --color-text: #000000;
  --color-border: #e5e7eb;
  --color-primary: #3b82f6;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: system-ui, -apple-system, sans-serif;
  background: var(--color-background);
  color: var(--color-text);
  line-height: 1.6;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  border-bottom: 2px solid var(--color-border);
  margin-bottom: 20px;
}

nav {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
}

nav a {
  padding: 10px 20px;
  border: 1px solid var(--color-border);
  text-decoration: none;
  color: var(--color-text);
}

nav a.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

button {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  background: white;
  cursor: pointer;
}

button:hover:not(:disabled) {
  background: #f3f4f6;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status-online {
  color: var(--color-online);
  font-size: 20px;
}

.status-offline {
  color: var(--color-offline);
  font-size: 20px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  margin: 20px 0;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.data-table th {
  font-weight: 600;
  background: #f9fafb;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #6b7280;
}

.error {
  color: #dc2626;
  padding: 12px;
  border: 1px solid #dc2626;
  background: #fee2e2;
  margin: 20px 0;
}
```

---

## Building for Production

```bash
# Development
ng serve

# Production build
ng build --configuration production

# Output in dist/ folder
```

---

## Environment Configuration

For different environments, create:
- `src/environments/environment.ts` (development)
- `src/environments/environment.prod.ts` (production)

```typescript
// environment.prod.ts
export const environment = {
  production: true,
  apiUrl: 'https://your-backend.com/api'
};
```

---

## Related Documents
- [01-system-architecture.md](./01-system-architecture.md) - System overview
- [03-spring-boot-backend.md](./03-spring-boot-backend.md) - Backend API
- [05-deployment.md](./05-deployment.md) - Deployment guide
