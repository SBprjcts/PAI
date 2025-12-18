import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-ead',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './ead.component.html',
  styleUrls: ['./ead.component.scss']
})
export class EadComponent {
  constructor(private auth: AuthService) {}

  expenses = [
    { date: '2025-09-01', amount: 450.75, vendor: 'Amazon', description: 'Office furniture', category: 'Supplies', anomalyScore: 98 },
    { date: '2025-09-10', amount: 120.0, vendor: 'Uber Eats', description: 'Team lunch', category: 'Food', anomalyScore: 85 },
    { date: '2025-09-12', amount: 29.99, vendor: 'Zoom', description: 'Monthly subscription', category: 'Software', anomalyScore: 45 }
  ];

  getSeverityColor(score: number): 'red' | 'yellow' | 'green' {
    if (score >= 95) return 'red';
    if (score >= 80) return 'yellow';
    return 'green';
  }
}
