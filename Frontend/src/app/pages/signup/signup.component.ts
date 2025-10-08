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
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, FormsModule, MatFormFieldModule, MatInputModule, ReactiveFormsModule, MatButtonModule, RouterModule],
  templateUrl: './signup.component.html',
  styleUrl: './signup.component.scss'
})
export class SignupComponent {
  companyFormControl = new FormControl('', [Validators.required]);
  emailFormControl = new FormControl('', [Validators.required, Validators.email]);
  passwordFormControl = new FormControl('', [Validators.required]);
  loading = false; error: string | null = null;

  constructor(private auth: AuthService, private router: Router) {}

  async onSubmit(e: Event) {
    e.preventDefault();
    if (this.companyFormControl.invalid || this.emailFormControl.invalid || this.passwordFormControl.invalid) return;
    this.loading = true; this.error = null;
    try {
      await this.auth.signup(
        this.companyFormControl.value!, this.emailFormControl.value!, this.passwordFormControl.value!
      );
      // optional: auto-login
      await this.auth.login(this.emailFormControl.value!, this.passwordFormControl.value!);
      this.router.navigateByUrl('/');
    } catch {
      this.error = 'Signup failed';
    } finally {
      this.loading = false;
    }
  }
}
