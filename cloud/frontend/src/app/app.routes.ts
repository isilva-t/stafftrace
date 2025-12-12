import { Routes } from '@angular/router';
import { CurrentStatus } from './components/current-status/current-status';
import { MonthlySummary } from './components/monthly-summary/monthly-summary';

export const routes: Routes = [
  { path: '', redirectTo: '/current', pathMatch: 'full' },
  { path: 'current', component: CurrentStatus },
  { path: 'monthly', component: MonthlySummary }
];
