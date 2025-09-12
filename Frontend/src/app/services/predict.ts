import { Injectable } from '@angular/core'; // Marks a class as a service that angular can inject into components
import { HttpClient } from '@angular/common/http'; // Used to send GET/POST requests to FastApi backend
import { environment } from '../../environments/environment'; // Imports environemt.ts file 
import { Observable } from 'rxjs'; // Angular HTTP returns observable for a stream of dats that can be watched

export interface PredictRequest{ // Defines the data to be sent to /predict
  vendor: string;
  description: string;
}

export interface PredictResponse{ // Defines the data to be received from /predict
  category: string;
  top: [string, number][]
}

export interface FeedbackRequest extends PredictRequest { // Defines the data to be sent to /feedback
  category: string;
  date?: string;
  amount?: number;
}

@Injectable({providedIn: 'root'}) // Creates a singleton service and makes it available throughout the application
export class Predict {
  private base = environment.API_BASE; // Stores the base URL for the API

  constructor(private http: HttpClient) {} // Constructor runs on service initialization, injecting HttpClient

  predict(body: PredictRequest): Observable<PredictResponse> {
    return this.http.post<PredictResponse>(`${this.base}/predict`, body); // Sends a POST request to the /predict endpoint
    // body is the request payload containing vendor and description
  }

  feedback(body: FeedbackRequest): Observable<{ status: string; message: string; }> {
    return this.http.post<{ status: string; message: string; }>('${this.base}/feedback', body); // Sends a POST request to the /feedback endpoint
  }
}


