import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductService, Product } from '../../../core/services/product.service';
import { CartService } from '../../../core/services/cart.service';
import { Observable } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './product-list.component.html',
  styleUrl: './product-list.component.css'
})
export class ProductListComponent implements OnInit {
  products$!: Observable<Product[]>;
  isAuthenticated = false;

  constructor(
    private productService: ProductService,
    private cartService: CartService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {
    this.products$ = this.productService.getProducts();
    this.authService.isAuthenticated$.subscribe(isAuth => this.isAuthenticated = isAuth);
  }

  addToCart(product: Product) {
    if (!this.isAuthenticated) {
      this.router.navigate(['/login']);
      return;
    }
    this.cartService.addToCart(product.id, 1).subscribe();
  }
}
