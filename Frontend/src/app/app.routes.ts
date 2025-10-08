// src/app/app.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  // Public routes
  {
    path: '',
    loadComponent: () =>
      import('./pages/home/home.component').then(m => m.HomeComponent),
    title: 'PAI | Home'
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./pages/login/login.component').then(m => m.LoginComponent),
    title: 'PAI | Login'
  },
  {
    path: 'signup',
    loadComponent: () =>
      import('./pages/signup/signup.component').then(m => m.SignupComponent),
    title: 'PAI | Signup'
  },

  // Protected routes
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
    title: 'PAI | Dashboard'
  },
  {
    path: 'ead',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./pages/ead/ead.component').then(m => m.EadComponent),
    title: 'PAI | Anomaly Detection'
  },

  // Wildcard route (everything else)
  { path: '**', redirectTo: 'login' }
];
