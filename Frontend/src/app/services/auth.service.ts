import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private base = 'http://localhost:5000/api';
  private accessToken: string | null = null;

  constructor(private http: HttpClient) {}

  // keep token only in memory
  get token() { return this.accessToken; }

  async signup(company: string, email: string, password: string) {
    return await firstValueFrom(
      this.http.post(`${this.base}/signup`, { company, email, password }, { withCredentials: true })
    );
  }

  async login(email: string, password: string) {
    const res: any = await firstValueFrom(
      this.http.post(`${this.base}/login`, { email, password }, { withCredentials: true })
    );
    this.accessToken = res.access_token;
    return res;
  }

  async refresh() {
    const res: any = await firstValueFrom(
      this.http.post(`${this.base}/refresh`, {}, { withCredentials: true })
    );
    this.accessToken = res.access_token;
    return res;
  }

  async me() {
    return await firstValueFrom(
      this.http.get(`${this.base}/me`, {
        withCredentials: true,
        headers: this.accessToken ? { Authorization: `Bearer ${this.accessToken}` } : {}
      })
    );
  }

  async logout() {
    await firstValueFrom(
      this.http.post(`${this.base}/logout`, {}, { withCredentials: true })
    );
    this.accessToken = null;
  }
}
