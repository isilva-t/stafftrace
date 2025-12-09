import { Injectable } from "@angular/core";
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from "rxjs";
import { LoginRequest, LoginResponse } from "../models/employee.model";
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})

export class AuthService {
  private apiUrl = `${environment.apiUrl}/auth`;
  private tokenKey = 'auth_token';

  constructor(private http: HttpClient) { }

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
