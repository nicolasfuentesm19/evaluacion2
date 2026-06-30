import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { AuditoriaService, AuditEvent } from '../../../core/services/auditoria.service';

@Component({
  selector: 'app-auditoria-dashboard',
  standalone: true,
  imports: [CommonModule, HttpClientModule],
  providers: [AuditoriaService],
  templateUrl: './auditoria-dashboard.component.html',
  styleUrls: ['./auditoria-dashboard.component.css']
})
export class AuditoriaDashboardComponent implements OnInit {
  events: AuditEvent[] = [];
  filteredEvents: AuditEvent[] = [];
  loading = false;
  error = '';
  selectedType = '';
  eventTypes: string[] = [];

  constructor(private auditoriaService: AuditoriaService) { }

  ngOnInit(): void {
    this.loadEvents();
  }

  loadEvents(): void {
    this.loading = true;
    this.error = '';
    this.auditoriaService.getEvents().subscribe({
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
      this.filteredEvents = this.events.filter(e => e.event_type === type);
    }
  }
}
