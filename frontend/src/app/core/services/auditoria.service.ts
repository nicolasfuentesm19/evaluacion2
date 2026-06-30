import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface AuditEvent {
  id: number;
  timestamp: string;
  user_email: string;
  event_type: string;
  description: string;
  ip_address?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuditoriaService {
  private baseUrl: string;

  constructor(private http: HttpClient, private apiService: ApiService) {
    this.baseUrl = this.apiService.baseUrl;
  }

  getEvents(): Observable<AuditEvent[]> {
    return this.http.get<AuditEvent[]>(`${this.baseUrl}/audit-events`);
  }
}
