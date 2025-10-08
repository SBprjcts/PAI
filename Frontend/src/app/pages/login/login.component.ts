import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  FormControl,
  FormGroupDirective,
  NgForm,
  Validators,
  FormsModule,
  ReactiveFormsModule,
} from '@angular/forms';
import { ErrorStateMatcher } from '@angular/material/core';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatButtonModule  } from '@angular/material/button';
import { AuthService } from '../../services/auth.service';
import { Router, RouterModule } from '@angular/router';



@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, MatFormFieldModule, MatInputModule, ReactiveFormsModule, MatButtonModule, RouterModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  emailFormControl = new FormControl('', [Validators.required, Validators.email]);
  passwordFormControl = new FormControl('', [Validators.required]);
  loading = false;
  error: string | null = null;

  constructor(private auth: AuthService, private router: Router) {}

  async onSubmit(e: Event) {
    e.preventDefault();
    if (this.emailFormControl.invalid || this.passwordFormControl.invalid) return;
    this.loading = true; this.error = null;
    try {
      await this.auth.login(this.emailFormControl.value!, this.passwordFormControl.value!);
      this.router.navigateByUrl('/dashboard'); // change to your dashboard route
    } catch (err: any) {
      this.error = 'Invalid email or password';
    } finally {
      this.loading = false;
    }
  }
}
