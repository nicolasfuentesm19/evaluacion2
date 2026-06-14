import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class FilesService {

  constructor(private http: HttpClient, private api: ApiService) { }

  getFiles() {
    return this.http.get<any[]>(`${this.api.baseUrl}/files/`);
  }

  getSpace() {
    return this.http.get<any>(`${this.api.baseUrl}/files/space`);
  }

  uploadFile(file: File, phoneNumber?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (phoneNumber) {
      formData.append('phone_number', phoneNumber);
    }
    return this.http.post<any>(`${this.api.baseUrl}/files/upload`, formData);
  }
}
