import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login-modal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login-modal.html',
  styleUrl: './login-modal.css'
})
export class LoginModal {
  @Output() closeModal = new EventEmitter<void>();
  @Output() loginSuccess = new EventEmitter<void>();

  username = '';
  password = '';
  error = '';
  loading = false;

  constructor(private authService: AuthService) { }

  login(): void {
    this.loading = true;
    this.error = '';

    this.authService.login(this.username, this.password).subscribe({
      next: () => {
        this.loading = false;
        this.loginSuccess.emit();
        this.closeModal.emit();
      },
      error: (err) => {
        this.error = 'Invalid credentials';
        this.loading = false;
        console.error(err);
      }
    });
  }

  cancel(): void {
    this.closeModal.emit();
  }
}
