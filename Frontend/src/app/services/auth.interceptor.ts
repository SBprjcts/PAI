import { inject } from '@angular/core';
import {
  HttpInterceptorFn, HttpRequest, HttpHandlerFn, HttpEvent, HttpErrorResponse
} from '@angular/common/http';
import { AuthService } from './auth.service';
import { BehaviorSubject, Observable, throwError, from } from 'rxjs';
import { catchError, filter, switchMap, take } from 'rxjs/operators';

let isRefreshing = false;
const refresh$ = new BehaviorSubject<string | null>(null);

const isAuthEndpoint = (url: string) =>
  url.endsWith('/api/login') || url.endsWith('/api/refresh') || url.endsWith('/api/signup');

export const authInterceptor: HttpInterceptorFn = (req: HttpRequest<any>, next: HttpHandlerFn): Observable<HttpEvent<any>> => {
  const auth = inject(AuthService);

  const headers: Record<string, string> = {};
  const token = auth.token;
  if (token && !isAuthEndpoint(req.url)) headers['Authorization'] = `Bearer ${token}`;

  const authed = req.clone({ withCredentials: true, setHeaders: headers });

  return next(authed).pipe(
    catchError((err: any) => {
      if (isAuthEndpoint(req.url) || !(err instanceof HttpErrorResponse) || err.status !== 401) {
        return throwError(() => err);
      }

      // 401 on a protected endpoint → try a single refresh
      if (!isRefreshing) {
        isRefreshing = true;
        refresh$.next(null);

        return from(auth.refresh()).pipe(                    // auth.refresh() returns a Promise<string>
          switchMap((newToken: string) => {
            isRefreshing = false;
            refresh$.next(newToken);

            const retryHeaders: Record<string, string> = { Authorization: `Bearer ${newToken}` };
            const retryReq = req.clone({ withCredentials: true, setHeaders: retryHeaders });
            return next(retryReq);                           // retry original request with new token
          }),
          catchError((refreshErr) => {
            isRefreshing = false;
            return throwError(() => refreshErr);
          })
        );
      }

      // If a refresh is already in flight, wait for it
      return refresh$.pipe(
        filter((t): t is string => t !== null),
        take(1),
        switchMap((t) => {
          const retryReq = req.clone({ withCredentials: true, setHeaders: { Authorization: `Bearer ${t}` } });
          return next(retryReq);
        })
      );
    })
  );
};
