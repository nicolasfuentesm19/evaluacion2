import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  public baseUrl: string = 'http://ecommerce-backend-alb-1181827508.us-east-1.elb.amazonaws.com'; // DNS estático del ALB
  constructor() { }
}
