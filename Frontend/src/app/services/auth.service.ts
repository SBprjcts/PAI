import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private base = ''; // was 'http://localhost:5000'
  private accessToken: string | null = null;

  constructor(private http: HttpClient) {}

  get token() { return this.accessToken; }

  // NEW: used by SignupComponent
  async signup(company: string, email: string, password: string) {
    return await firstValueFrom(
      this.http.post(`${this.base}/api/signup`, { company, email, password }, { withCredentials: true })
    );
  }

  async login(email: string, password: string) {
    const res: any = await firstValueFrom(
      this.http.post(`${this.base}/api/login`, { email, password }, { withCredentials: true })
    );
    this.accessToken = res.access_token;
    return res;
  }

  // used by interceptor; returns Promise<string>
  async refresh(): Promise<string> {
    const res: any = await firstValueFrom(
      this.http.post(`${this.base}/api/refresh`, {}, { withCredentials: true })
    );
    this.accessToken = res.access_token;
    return this.accessToken!;
  }

  async me() {
    return await firstValueFrom(
      this.http.get(`${this.base}/api/me`, { withCredentials: true })
    );
  }

  async logout() {
    await firstValueFrom(this.http.post(`${this.base}/api/logout`, {}, { withCredentials: true }));
    this.accessToken = null;
  }
}
