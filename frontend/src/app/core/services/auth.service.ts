import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiService } from './api.service';
import { BehaviorSubject, tap } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private tokenKey = 'ecommerce_token';
  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasToken());
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  constructor(private http: HttpClient, private api: ApiService) { }

  private hasToken(): boolean {
    return !!localStorage.getItem(this.tokenKey);
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  login(credentials: any) {
    const formData = new URLSearchParams();
    formData.set('username', credentials.email);
    formData.set('password', credentials.password);

    return this.http.post<any>(`${this.api.baseUrl}/token`, formData.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }).pipe(
      tap(res => {
        localStorage.setItem(this.tokenKey, res.access_token);
        this.isAuthenticatedSubject.next(true);
      })
    );
  }

  register(userData: any) {
    return this.http.post(`${this.api.baseUrl}/users/`, userData);
  }

  logout() {
    localStorage.removeItem(this.tokenKey);
    this.isAuthenticatedSubject.next(false);
  }
}
