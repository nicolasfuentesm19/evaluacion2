import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CartService, Cart } from '../../../core/services/cart.service';
import { Observable } from 'rxjs';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-cart',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './cart.component.html',
  styleUrl: './cart.component.css'
})
export class CartComponent implements OnInit {
  cart$!: Observable<Cart | null>;
  isProcessing = false;
  paymentSuccess = false;

  constructor(private cartService: CartService) {}

  ngOnInit() {
    this.cartService.getCart().subscribe();
    this.cart$ = this.cartService.cart$;
  }

  removeItem(productId: number) {
    this.cartService.removeFromCart(productId).subscribe();
  }

  getTotal(cart: Cart): number {
    return cart.items.reduce((acc, item) => acc + (item.product.price * item.quantity), 0);
  }

  checkout() {
    this.isProcessing = true;
    this.cartService.checkout().subscribe({
      next: (res) => {
        this.isProcessing = false;
        if (res.url_pago) {
          window.location.href = res.url_pago; // Redirigir a Mercado Pago
        } else {
          this.paymentSuccess = true;
        }
      },
      error: (err) => {
        this.isProcessing = false;
        alert(err.error?.detail || 'Hubo un error procesando el pago');
      }
    });
  }
}
