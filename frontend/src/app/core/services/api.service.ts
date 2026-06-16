import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  public baseUrl: string = 'http://3.93.197.168:8000'; // IP pública inyectada tras reiniciar Fargate
  constructor() { }
}
