import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  // En producción esto debería venir de environments
  public readonly baseUrl = 'http://98.89.29.74:8000';
}
