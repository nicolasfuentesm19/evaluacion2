import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  public baseUrl: string = 'http://54.208.151.87:8000'; // IP pública inyectada tras reiniciar Fargate
  constructor() { }
}
