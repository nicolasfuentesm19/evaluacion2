import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

export interface AuditEvent {
  id: number;
  timestamp: string;
  user_email: string;
  event_type: string;
  description: string;
  ip_address?: string;
}

@Component({
  selector: 'app-auditoria-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './auditoria-dashboard.component.html',
  styleUrls: ['./auditoria-dashboard.component.css']
})
export class AuditoriaDashboardComponent implements OnInit {
  private http = inject(HttpClient);
  private backendUrl = 'http://ecommerce-backend-alb-1181827508.us-east-1.elb.amazonaws.com';

  events: AuditEvent[] = [];
  filteredEvents: AuditEvent[] = [];
  loading = false;
  error = '';
  selectedType = '';
  eventTypes: string[] = [];

  ngOnInit(): void {
    this.loadEvents();
  }

  loadEvents(): void {
    this.loading = true;
    this.error = '';
    this.http.get<AuditEvent[]>(`${this.backendUrl}/audit-events`).subscribe({
      next: (data: AuditEvent[]) => {
        this.events = data;
        this.filteredEvents = data;
        this.eventTypes = [...new Set(data.map((e: AuditEvent) => e.event_type))];
        this.loading = false;
      },
      error: (err: unknown) => {
        this.error = 'Error cargando eventos de auditoría';
        this.loading = false;
        console.error(err);
      }
    });
  }

  filterByType(type: string): void {
    this.selectedType = type;
    if (!type) {
      this.filteredEvents = this.events;
    } else {
      this.filteredEvents = this.events.filter((e: AuditEvent) => e.event_type === type);
    }
  }
}
