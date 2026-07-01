import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { ApiService } from '../../../../core/services/api.service';
import { CartService } from '../../../../core/services/cart.service';

@Component({
  selector: 'app-payment-success',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './payment-success.component.html'
})
export class PaymentSuccessComponent implements OnInit {
  status: 'processing' | 'success' | 'error' = 'processing';
  message: string = 'Estamos confirmando tu pago...';
  collectionId: string = '';

  constructor(
    private route: ActivatedRoute,
    private http: HttpClient,
    private api: ApiService,
    private cartService: CartService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      const preferenceId = params['preference_id'] || '';
      const collectionId = params['collection_id'];
      const status = params['status'];

      if (!collectionId || status !== 'approved') {
        this.status = 'error';
        this.message = 'No se pudo confirmar el pago o el pago no fue aprobado.';
        return;
      }

      this.collectionId = collectionId;
      this.confirmPayment(preferenceId, collectionId, status);
    });
  }

  confirmPayment(preferenceId: string, collectionId: string, status: string) {
    this.http.post(`${this.api.baseUrl}/checkout/confirm`, {
      preference_id: preferenceId,
      collection_id: collectionId,
      status: status
    }).subscribe({
      next: (res) => {
        this.status = 'success';
        this.message = '¡Tu compra ha sido confirmada exitosamente! Se ha enviado un correo con el detalle.';
        this.cartService.getCart().subscribe(); // Refresh cart to empty state
      },
      error: (err) => {
        console.error(err);
        this.status = 'error';
        this.message = 'Ocurrió un error al registrar el pago en nuestro sistema.';
      }
    });
  }
}
