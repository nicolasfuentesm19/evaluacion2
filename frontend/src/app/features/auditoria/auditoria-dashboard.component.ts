import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuditoriaService, AuditEvent } from '../../../core/services/auditoria.service';

@Component({
  selector: 'app-auditoria-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './auditoria-dashboard.component.html',
  styleUrls: ['./auditoria-dashboard.component.css']
})
export class AuditoriaDashboardComponent implements OnInit {
  events: AuditEvent[] = [];
  loading = false;
  error = '';

  constructor(private auditoriaService: AuditoriaService) { }

  ngOnInit(): void {
    this.loadEvents();
  }

  loadEvents(): void {
    this.loading = true;
    this.auditoriaService.getEvents().subscribe({
      next: (data) => {
        this.events = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Error loading events';
        this.loading = false;
        console.error(err);
      }
    });
  }
}
