import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { Router, RouterLink } from '@angular/router';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.component.html',
  styles: [`
    .auth-container { max-width: 400px; margin: 4rem auto; }
    .error-msg { color: var(--danger-color); margin-bottom: 1rem; font-size: 0.9rem; }
  `]
})
export class RegisterComponent {
  email = '';
  password = '';
  error = '';
  success = '';
  
  isRegistered = false;
  verificationCode = '';

  constructor(private authService: AuthService, private router: Router) {}

  onSubmit() {
    this.error = '';
    this.authService.register({ email: this.email, password: this.password }).subscribe({
      next: () => {
        this.isRegistered = true;
        this.success = 'Se ha enviado un código de verificación a tu correo.';
      },
      error: (err) => this.error = err.error?.detail || 'Error al registrar'
    });
  }

  onVerify() {
    this.error = '';
    this.authService.verify({ email: this.email, code: this.verificationCode }).subscribe({
      next: () => {
        this.success = 'Cuenta verificada con éxito. Redirigiendo...';
        setTimeout(() => this.router.navigate(['/login']), 2000);
      },
      error: (err) => this.error = err.error?.detail || 'Código inválido o error al verificar'
    });
  }
}
