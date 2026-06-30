import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiService } from './api.service';
import { Observable } from 'rxjs';

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

  constructor(private http: HttpClient, private apiService: ApiService) { }

  getEvents(): Observable<AuditEvent[]> {
    return this.http.get<AuditEvent[]>(`${this.apiService.baseUrl}/audit-events`);
  }
}
