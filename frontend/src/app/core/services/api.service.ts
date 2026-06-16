import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  public baseUrl: string = 'http://44.203.246.12:8000'; // IP pública inyectada tras reiniciar Fargate
  constructor() { }
}
