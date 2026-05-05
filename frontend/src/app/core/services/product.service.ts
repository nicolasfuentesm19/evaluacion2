import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiService } from './api.service';
import { Observable } from 'rxjs';

export interface Product {
  id: number;
  title: string;
  description: string;
  price: number;
  image_url: string;
}

@Injectable({
  providedIn: 'root'
})
export class ProductService {
  constructor(private http: HttpClient, private api: ApiService) { }

  getProducts(): Observable<Product[]> {
    return this.http.get<Product[]>(`${this.api.baseUrl}/products/`);
  }
}
