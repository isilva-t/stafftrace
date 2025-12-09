import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CurrentStatus } from './components/current-status/current-status';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, CurrentStatus],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  title = 'frontend'
}
