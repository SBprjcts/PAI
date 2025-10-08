// src/app/services/auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';
import { from, switchMap, catchError, throwError } from 'rxjs';

export const AuthInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);

  const headers: Record<string, string> = {};
  if (auth.token) {
    headers['Authorization'] = `Bearer ${auth.token}`;
  }

  const authedReq = req.clone({
    withCredentials: true,
    setHeaders: headers,
  });

  return next(authedReq).pipe(
    catchError((err) => {
      if (err.status === 401) {
        return from(auth.refresh()).pipe(
          switchMap(() => {
            const retryHeaders: Record<string, string> = {};
            if (auth.token) {
              retryHeaders['Authorization'] = `Bearer ${auth.token}`;
            }

            const retryReq = req.clone({
              withCredentials: true,
              setHeaders: retryHeaders,
            });

            return next(retryReq);
          }),
          catchError(() => throwError(() => err))
        );
      }

      return throwError(() => err);
    })
  );
};
