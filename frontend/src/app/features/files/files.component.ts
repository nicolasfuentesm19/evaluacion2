import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { FilesService } from '../../core/services/files.service';

@Component({
  selector: 'app-files',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './files.component.html',
  styles: [`
    .dashboard-container { padding: 2rem 0; max-width: 800px; margin: 0 auto; }
    h2 { margin-bottom: 2rem; font-size: 1.8rem; font-weight: 700; color: var(--text-primary); }
    h3 { margin-bottom: 1rem; font-size: 1.2rem; font-weight: 600; color: var(--text-primary); border-bottom: 1px solid var(--card-border); padding-bottom: 0.75rem; }
    .card { background: var(--card-bg); padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; border: 1px solid var(--card-border); box-shadow: var(--card-shadow); }
    .progress-bar { height: 12px; background: #f4f4f5; border-radius: 6px; overflow: hidden; margin: 1rem 0; border: 1px solid var(--card-border); }
    .progress-fill { height: 100%; background-color: var(--accent-color); transition: width 0.4s var(--transition-ease); }
    .file-list { list-style: none; padding: 0; }
    .file-list li { padding: 1rem 0; border-bottom: 1px solid #f4f4f5; display: flex; justify-content: space-between; align-items: center; }
    .file-list li:last-child { border-bottom: none; padding-bottom: 0; }
  `]
})
export class FilesComponent implements OnInit {
  files: any[] = [];
  spaceInfo: any = null;
  selectedFile: File | null = null;
  phoneNumber: string = '';
  isUploading = false;
  error = '';
  success = '';

  constructor(private filesService: FilesService) {}

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.filesService.getSpace().subscribe(data => this.spaceInfo = data);
    this.filesService.getFiles().subscribe(data => this.files = data);
  }

  onFileSelected(event: any) {
    if (event.target.files.length > 0) {
      this.selectedFile = event.target.files[0];
    }
  }

  onUpload() {
    if (!this.selectedFile) return;
    this.isUploading = true;
    this.error = '';
    this.success = '';

    this.filesService.uploadFile(this.selectedFile, this.phoneNumber).subscribe({
      next: () => {
        this.success = 'Archivo subido con éxito';
        this.selectedFile = null;
        this.phoneNumber = '';
        this.isUploading = false;
        this.loadData();
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error al subir el archivo';
        this.isUploading = false;
      }
    });
  }
}
