import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  public baseUrl: string = 'http://100.58.238.106:8000'; // IP pública inyectada tras reiniciar Fargate
  constructor() { }
}
