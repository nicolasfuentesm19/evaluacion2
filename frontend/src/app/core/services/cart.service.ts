import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiService } from './api.service';
import { Product } from './product.service';
import { BehaviorSubject, tap } from 'rxjs';

export interface CartItem {
  id: number;
  product_id: number;
  quantity: number;
  product: Product;
}

export interface Cart {
  id: number;
  user_id: number;
  items: CartItem[];
}

@Injectable({
  providedIn: 'root'
})
export class CartService {
  private cartSubject = new BehaviorSubject<Cart | null>(null);
  public cart$ = this.cartSubject.asObservable();

  constructor(private http: HttpClient, private api: ApiService) { }

  getCart() {
    return this.http.get<Cart>(`${this.api.baseUrl}/cart/`).pipe(
      tap(cart => this.cartSubject.next(cart))
    );
  }

  addToCart(productId: number, quantity: number = 1) {
    return this.http.post<Cart>(`${this.api.baseUrl}/cart/items/`, {
      product_id: productId,
      quantity: quantity
    }).pipe(
      tap(cart => this.cartSubject.next(cart))
    );
  }

  removeFromCart(productId: number) {
    return this.http.delete<Cart>(`${this.api.baseUrl}/cart/items/${productId}`).pipe(
      tap(cart => this.cartSubject.next(cart))
    );
  }

  checkout() {
    return this.http.post<any>(`${this.api.baseUrl}/checkout/`, {}).pipe(
      tap(() => this.cartSubject.next(null)) // Vaciar carrito localmente tras éxito
    );
  }
}
