import { Routes } from '@angular/router';
import { CurrentStatus } from './components/current-status/current-status';
import { DailyReport } from './components/daily-report/daily-report';
import { MonthlySummary } from './components/monthly-summary/monthly-summary';
import { EmployeeDetail } from './components/employee-detail/employee-detail';
import { Architecture } from './components/architecture/architecture'

export const routes: Routes = [
  { path: '', redirectTo: '/current', pathMatch: 'full' },
  { path: 'current', component: CurrentStatus },
  { path: 'daily', component: DailyReport },
  { path: 'monthly', component: MonthlySummary },
  { path: 'about', component: Architecture },
  { path: 'employee/:id', component: EmployeeDetail }
];
