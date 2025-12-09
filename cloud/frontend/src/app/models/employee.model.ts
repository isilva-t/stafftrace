export interface EmployeeStatus {
  employeeId: number;
  employeeName: string;
  isPresent: boolean;
  currentArea: string;
  lastSeen: string;
}

export interface DailyPresence {
  employeeId: number;
  employeeName: string;
  date: string;
  firstSeen: string | null;
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

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  message: string;
}
