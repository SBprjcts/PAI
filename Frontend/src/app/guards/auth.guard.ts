// src/app/guards/auth.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  try {
    // Try to get user info (using in-memory token + /refresh fallback)
    if (!auth.token) await auth.refresh();
    await auth.me();
    return true;
  } catch (err) {
    // Not authenticated: redirect to login
    router.navigate(['/login']);
    return false;
  }
};
