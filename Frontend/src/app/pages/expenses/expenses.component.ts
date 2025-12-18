import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ExpenseService } from '../../services/expense.service';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { RouterModule } from '@angular/router';

interface Expense {
  id?: number;
  date: string;
  amount: number;
  vendor: string;
  description: string;
  category: string;
}

@Component({
  selector: 'app-expenses',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterModule],
  templateUrl: './expenses.component.html',
  styleUrls: ['./expenses.component.scss']
})
export class ExpensesComponent {
  expenses: Expense[] = [];
  filteredExpenses: Expense[] = [];
  editIndex: number | null = null;
  editForm!: FormGroup;
  sortOrder: 'newest' | 'oldest' = 'newest';
  searchTerm = '';
  selectedCategory = 'All';
  monthlyTotals: { [month: string]: number } = {};

  constructor(private expenseService: ExpenseService, private fb: FormBuilder) {
    this.loadExpenses();
  }

  loadExpenses() {
    this.expenseService.getExpenses().subscribe((res: Expense[]) => {
      this.expenses = this.sortExpenses(res);
      this.filteredExpenses = [...this.expenses];
      this.calculateMonthlyTotals();
    });
  }

  sortExpenses(expenses: Expense[]): Expense[] {
    return expenses.sort((a, b) =>
      this.sortOrder === 'newest'
        ? new Date(b.date).getTime() - new Date(a.date).getTime()
        : new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }

  toggleSortOrder() {
    this.sortOrder = this.sortOrder === 'newest' ? 'oldest' : 'newest';
    this.filteredExpenses = this.sortExpenses([...this.filteredExpenses]);
  }

  startEdit(index: number) {
    this.editIndex = index;
    const exp = this.filteredExpenses[index];
    this.editForm = this.fb.group({
      date: [exp.date],
      amount: [exp.amount],
      vendor: [exp.vendor],
      description: [exp.description],
      category: [exp.category]
    });
  }

  cancelEdit() {
    this.editIndex = null;
  }

  saveEdit(index: number) {
    const updated = { ...this.filteredExpenses[index], ...this.editForm.value };
    this.expenseService.updateExpense(updated).subscribe(() => {
      this.filteredExpenses[index] = updated;
      this.expenses = this.filteredExpenses;
      this.editIndex = null;
      this.calculateMonthlyTotals();
    });
  }

  deleteExpense(id?: number) {
    if (!id) return;
    if (!confirm('Are you sure you want to delete this expense?')) return;

    this.expenseService.deleteExpense(id).subscribe(() => {
      this.expenses = this.expenses.filter(e => e.id !== id);
      this.filteredExpenses = this.filteredExpenses.filter(e => e.id !== id);
      this.calculateMonthlyTotals();
    });
  }

  searchExpenses() {
    const term = this.searchTerm.toLowerCase();
    this.filteredExpenses = this.expenses.filter(exp =>
      (this.selectedCategory === 'All' || exp.category === this.selectedCategory) &&
      (exp.vendor.toLowerCase().includes(term) ||
       exp.description.toLowerCase().includes(term) ||
       exp.category.toLowerCase().includes(term))
    );
  }

  calculateMonthlyTotals() {
    this.monthlyTotals = {};
    for (const exp of this.expenses) {
      const date = new Date(exp.date);
      const monthKey = `${date.toLocaleString('default', { month: 'long' })} ${date.getFullYear()}`;
      if (!this.monthlyTotals[monthKey]) {
        this.monthlyTotals[monthKey] = 0;
      }
      this.monthlyTotals[monthKey] += exp.amount;
    }
  }

  get uniqueCategories(): string[] {
    return this.expenses
      .map(e => e.category)
      .filter((value, index, self) => self.indexOf(value) === index);
  }

  get formattedMonthlyTotals() {
    return Object.entries(this.monthlyTotals).sort(
      ([a], [b]) => new Date(b).getTime() - new Date(a).getTime()
    );
  }
}
