import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ExpenseService } from '../../services/expense.service';

@Component({
  selector: 'app-expense',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './expense.component.html',
  styleUrls: ['./expense.component.scss']
})
export class ExpenseComponent {
  expenseForm: FormGroup;
  successMessage: string | null = null;

  constructor(private fb: FormBuilder, private expenseService: ExpenseService, private router: Router) {
    this.expenseForm = this.fb.group({
      date: ['', Validators.required],
      amount: ['', [Validators.required, Validators.min(0.01)]],
      vendor: ['', Validators.required],
      description: [''],
      category: ['', Validators.required]
    });
  }

  submitExpense() {
    if (this.expenseForm.valid) {
      const data = this.expenseForm.value;
      this.expenseService.addExpense(data).subscribe({
        next: (res) => {
          console.log('✅ Expense submitted:', res);
          this.successMessage = '✅ Expense submitted successfully!';
          this.expenseForm.reset();

          // Delay redirect (1.5 seconds)
          setTimeout(() => {
            this.router.navigate(['/expenses']);
          }, 1500);
        },
        error: (err) => {
          console.error('❌ Failed to submit expense:', err);
        }
      });
    }
  }
}
