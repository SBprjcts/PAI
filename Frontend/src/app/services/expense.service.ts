// src/app/services/expense.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ExpenseService {
  private apiUrl = 'http://localhost:5000/api/expense';  // Update if hosted differently

  constructor(private http: HttpClient) {}

  addExpense(expense: any): Observable<any> {
    return this.http.post(this.apiUrl, expense);
  }

  getExpenses(): Observable<any[]> {
    return this.http.get<any[]>('http://localhost:5000/api/expense');
  }

  updateExpense(expense: any): Observable<any> {
    return this.http.put(`http://localhost:5000/api/expense/${expense.id}`, expense);
  }

  deleteExpense(id: number): Observable<any> {
    return this.http.delete(`http://localhost:5000/api/expense/${id}`);
  }
}
