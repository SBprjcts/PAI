import { Component } from '@angular/core';
import { Form, FormBuilder, Validators, FormGroup, ReactiveFormsModule} from '@angular/forms';
import { Predict, PredictResponse } from '../../services/predict';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-predict.comp',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './predict.comp.html',
  styleUrl: './predict.comp.scss'
})
export class PredictComp { 

  loading = false; // Property/attribute that Indicates if a prediction request to backend is in progress
  showManual = false // Property/attribute that indicates if manual correction form is displayed to user
  allCategories: string[] = []
  error: string | null = null; // Stores error messages, can be string or null
  result: PredictResponse | null = null; // Stores the prediction result
  form: FormGroup; // Form group for vendor and description inputs
  correctionForm: FormGroup; // Form group for category correction input


  constructor(private fb: FormBuilder, private api: Predict) { // Constructor injects FormBuilder and Predict service
   this.form = this.fb.group({ // Initializes main prediction form with validators
    date: ['', [Validators.required]], // Date field must be required
    amount: ['', [Validators.required, Validators.min(0.01), Validators.minLength(1), Validators.maxLength(12)]], // Amount field with required and min value validators
    vendor: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(30)]], // Vendor field with required, min length, and max length validators
    description: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(255)]]
    });
    
    this.correctionForm = this.fb.group({
      category: [''] // Initializes correction form with a single category field and no validators (means its optional)
    });
    }
    
    ngOnInit(): void {
      this.api.getCategories().subscribe({
        next: (r) => this.allCategories = [...new Set(r.categories)].sort((a,b) => a.localeCompare(b)), // Cleaned (no dupes), sorted array of cats
        error: () => this.allCategories = this.allCategories ?? []  // If the request fails, keep existing categories or default to empty
      });
    }

    enforceTwoDecimals(event: any) {
      const input = event.target as HTMLInputElement; // Retrieves input from user (amount) 
      let value = input.value;
      if (value.includes('.')) {
        const [integerPart, decimalPart] = value.split('.');
        if (decimalPart.length > 2) {
          value = `${integerPart}.${decimalPart.slice(0, 2)}`;  // SPlits and controls length of string after decimal
          }
        }
        input.value = value; // Updates input if trimmed
        this.form.get('amount')?.setValue(value, { emitEvent: false }); // Updates in the form 
      } 
    
    enforceCharLimit(event: any, limit: number) { 
      const input = event.target as HTMLInputElement;
      let value = input.value;
      if (input.value.length > limit) {
        value = value.substring(0, limit);
        input.value = value;
      }
      const controlName = input.getAttribute('formControlName');
      if (controlName) {
        this.form.get(controlName)?.setValue(value, { emitEvent: false });
      }
    }

    submitPredict() {
      this.error = null; // Resets error message before predicting
      this.result = null; // Resets previous prediction result
      if (this.form.invalid) { // Checks if the form is valid and if not, sets an error message and exits the function
        this.error = 'Please enter valid vendor and description (3-50 chars for vendor, 3-100 chars for description).';
        return;
      }
      this.loading = true // Sets loading to true to indicate a request is in progress
      const { vendor, description } = this.form.value as { vendor: string; description: string }; // Extracts vendor and description from form values
      this.api.predict({ vendor, description }).subscribe({ // Calls the predict method from the Predict service (api) and subscribes to the observable
        next: (res) => { this.result = res; this.loading = false; }, // On success, stores the result and sets loading to false
        error: (err) => { this.error = err?.error?.detail ?? 'Prediction failed.'; this.loading = false; } // On error, stores the error message and sets loading to false
      });
    }

    normalizeCategory(e: Event) {
      const el = e.target as HTMLInputElement; // Grabs DOM element from category box, tells typescript its <input> element
      el.value = el.value.replace(/\s+/g, ' ').trimStart(); // Replaces mutliple spaces with a single space and removes space at start of text
       this.correctionForm.get('category')?.setValue(el.value, { emitEvent: false }); // Updates form control for category with the cleaned value
    }

    get canSubmitCorrection(): boolean {
      const v = (this.correctionForm.get('category')?.value || '').trim(); // Gets the current category typed or '' for none
      const predicted = (this.result?.category || '').trim(); // removes leading and trailing spaces
      return v.length > 0 && v.length <= 30 && v.toLowerCase() !== predicted.toLowerCase(); // Button olnly enabled when all conditions met
    }

    acceptPrediction() {
      this.quickCorrect(this.result?.category);
    }

    quickCorrect(cat?: string) {
      this.correctionForm.setValue({ category: cat});
      this.submitFeedback();
    }

    submitFeedback() {
      if (!this.result) return; // If there's no prediction result, exits the function
      const category = (this.correctionForm.value.category || '').toString().trim(); // Extracts and trims the category from the correction form
      const { vendor, description, date, amount} = this.form.value as { vendor: string; description: string; date: string; amount: number }; // Extracts vendor and description from the main form
      if (!category) { this.error = 'Enter a corrected category.'; return; } // If category is empty, sets an error message and exits the function
      this.api.feedback({ vendor, description, date, amount, category }).subscribe({
        next: () => {
          this.correctionForm.reset(); // Resets the correction form on successful feedback submission
          alert('Thanks — your correction was recorded.')
        },
        error: (err) => { this.error = err?.error?.detail ?? 'Feedback failed.'; }
      });
    }

  }




