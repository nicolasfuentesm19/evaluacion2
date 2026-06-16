import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  // En producción esto debería venir de environments
  public readonly baseUrl = 'http://98.88.76.33:8000';
}
