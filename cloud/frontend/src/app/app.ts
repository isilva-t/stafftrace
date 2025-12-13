import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { LoginModal } from './components/login-modal/login-modal';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, LoginModal, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  title = 'frontend'
  showLoginModal = false;

  constructor(public authService: AuthService) { }

  openLogin(): void {
    this.showLoginModal = true;
  }

  closeLogin(): void {
    this.showLoginModal = false;
  }

  handleLoginSuccess(): void {
    window.location.reload();
  }

  logout(): void {
    this.authService.logout();
    window.location.reload();
  }
}
