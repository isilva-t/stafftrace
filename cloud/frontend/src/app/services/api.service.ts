import { Injectable } from "@angular/core";
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from "rxjs";
import { AuthService } from "./auth.service";
import {
  EmployeeStatus,
  DailyPresence,
  MonthlyPresence,
} from '../models/employee.model';
import { AgentDowntime } from "../models/downtime.model";
import { AgentHealth } from "../models/agent-health.model";
import { environment } from "../../environments/environment";

@Injectable({
  providedIn: 'root'
})

export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) { }

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

  getDowntimes(date: string): Observable<AgentDowntime[]> {
    return this.http.get<AgentDowntime[]>(
      `${this.apiUrl}/downtimes?date=${date}`,
      { headers: this.getHeaders() }
    );
  }

  getAgentHealth(): Observable<AgentHealth[]> {
    return this.http.get<AgentHealth[]>(
      `${this.apiUrl}/agent-health`,
      { headers: this.getHeaders() }
    );
  }
}
