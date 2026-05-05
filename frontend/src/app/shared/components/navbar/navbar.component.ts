import { Component } from '@angular/core';
import { RouterLink, Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { CartService } from '../../../core/services/cart.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterLink, CommonModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css'
})
export class NavbarComponent {
  isAuthenticated$ = this.authService.isAuthenticated$;
  cart$ = this.cartService.cart$;

  constructor(private authService: AuthService, private cartService: CartService, private router: Router) {
    this.cartService.getCart().subscribe(); // Fetch initial cart state
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
