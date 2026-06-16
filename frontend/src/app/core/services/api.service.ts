import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  // En producción esto debería venir de environments
  public readonly baseUrl = 'http://18.205.191.199:8000';
}
