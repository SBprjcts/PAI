import { Component } from '@angular/core';
import { Form, FormBuilder, Validators, FormGroup, ReactiveFormsModule} from '@angular/forms';
import { Predict, PredictResponse } from '../../services/predict';
import { CommonModule } from '@angular/common';
import { formatDate } from '@angular/common';


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
  selectedCategory: string | null = null; // User's current selected chip to stay dark
  topChips: string[] = []; // Ordered list of suggested chips


  private normalize(s: string | null | undefined): string {
    return (s ?? '').toLowerCase().replace(/\s+/g, ' ').trim();
  }

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
      next: (r) => { 
        const keys = [...new Set(
          (r.categories ?? [])
            .map(c => (c ?? '').toString().trim().toLowerCase()) // Normalize to lowercase and trim spaces
            .filter(Boolean)
        )];

      // Title Case inline (handles hyphenated words too)
      this.allCategories = keys
        .map(k =>
          k.split(' ')
           .map(w => w.split('-')
             .map(p => p ? p.charAt(0).toUpperCase() + p.slice(1) : p)
             .join('-')
           )
           .join(' ')
        )
        .sort((a, b) => a.localeCompare(b));
        },
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

    submitPredict() { // Now called when user presses continue button
      this.error = null; // Resets error message before predicting
      this.result = null; // Resets previous prediction result
      if (this.form.invalid) { // Checks if the form is valid and if not, sets an error message and exits the function
        this.error = 'Please enter valid vendor and description (3-50 chars for vendor, 3-100 chars for description).';
        return;
      }
      this.loading = true // Sets loading to true to indicate a request is in progress
      const { vendor, description } = this.form.value as { vendor: string; description: string }; // Extracts vendor and description from form values
      this.api.predict({ vendor, description }).subscribe({ // Calls the predict method from the Predict service (api) and subscribes to the observable
        next: (res) => { this.result = res; this.loading = false; this.initChipsFromResult(); }, // On success, stores the result and sets loading to false
        error: (err) => { this.error = err?.error?.detail ?? 'Prediction failed.'; this.loading = false; } // On error, stores the error message and sets loading to false
      });
    }

    normalizeCategory(e: Event) {
      const el = e.target as HTMLInputElement; // Grabs DOM element from category box, tells typescript its <input> element
      const raw = el.value; // Gets the raw value from the input box
      const normalized = raw.replace(/\s+/g, ' ').trimStart(); // Normalizes spaces: Replaces multiple spaces with a single space and removes space at start of text
      el.value = normalized; // Replaces mutliple spaces with a single space and removes space at start of text

      const ctrl = this.correctionForm.get('category');

      // 1) Clear chip as soon as typed text (normalized) diverges from current selection
      if (this.selectedCategory) {
        const currSelNorm = this.normalize(this.selectedCategory);
        if (this.normalize(normalized) !== currSelNorm) {
          this.selectedCategory = null; // clear current chip
        }
      }

      // 2) If the normalized typed text exactly matches any suggestion, auto-select that chip
      const match = (this.topChips ?? []).find(
        name => this.normalize(name) === this.normalize(normalized)
      );

      if (match) {
        // lock to the canonical chip label (preserves proper case/spaces)
        this.selectedCategory = match;
        if (el.value !== match) el.value = match;
        ctrl?.setValue(match, { emitEvent: false });
      }

      // 3) Otherwise, keep the normalized free-text (no chip selected)
      ctrl?.setValue(normalized, { emitEvent: false });

      // 4) If user fully cleared the input, ensure no chip is selected
      if (!normalized) {
        this.selectedCategory = null;
      }
    }

    get filteredCategories(): string[] {
    const q = (this.correctionForm.get('category')?.value || '').toLowerCase().trim(); // Gets the current category typed or '' for none
    const all = this.allCategories ?? []; // Ensures allCategories is defined and is an array 
    if (!q) return all.slice(0, 8); // If no query, return first 8 categories
    const starts = all.filter(c => c.toLowerCase().startsWith(q)); // Categories that start with the query
    const contains = all.filter(c => !c.toLowerCase().startsWith(q) && c.toLowerCase().includes(q)); // Categories that contain the query but don't start with it
    return [...starts, ...contains].slice(0, 8); // Combines both lists and returns the first 8 unique categories (not nested)
    }

    get canSubmitCorrection(): boolean {
      const v = (this.correctionForm.get('category')?.value || '').trim(); // Gets the current category typed or '' for none
      const predicted = (this.result?.category || '').trim(); // removes leading and trailing spaces
      return v.length > 0 && v.length <= 30 && v.toLowerCase(); // Button olnly enabled when all conditions met
    }

    acceptPrediction() {
      this.quickCorrect(this.result?.category);
    }

    quickCorrect(cat?: string) {
      this.correctionForm.setValue({ category: cat});
      this.submitFeedback();
    }

    clearManual() {
      this.selectedCategory = null; 
      this.correctionForm.patchValue({ category: '' });
    }

    initChipsFromResult(): void {
      if (!this.result) return;
      const predicted = (this.result.category || '').trim(); // Cleans predicted category
      const tops = (this.result.top || []) // Array of [category, score] tuples
        .map((t: [string, number]) => (t?.[0] || '').trim()) // Cleans each category
        .filter(Boolean); // Removes any empty strings
        this.topChips = Array.from(new Set([predicted, ...tops])); // Ensures uniqueness while preserving order
        this.selectedCategory = predicted; // Sets the selected category to the predicted one
        this.correctionForm.patchValue({ category: predicted }); // Updates the correction form with the predicted category
    }

    selectCategory(name: string): void {
      this.selectedCategory = name; // Updates the selected category to the one clicked
      this.correctionForm.patchValue({ category: name }); // Updates the correction form with the selected category
    }

    submitFeedback() {
      if (!this.result) return; // If there's no prediction result, exits the function

      const rawCat = (this.correctionForm.value.category ?? '').toString();
      const rawVendor = (this.form.value.vendor ?? '').toString();
      const rawDesc = (this.form.value.description ?? '').toString();
      const rawDate = (this.form.value.date ?? '').toString();
      const rawAmount = (this.form.value.amount ?? '').toString();


      const category = this.normalize(rawCat); 
      const vendor = this.normalize(rawVendor);
      const description = this.normalize(rawDesc);

      // Coerce amount -> number; strip commas/spaces
      const amountNum = Number(rawAmount.toString().replace(/,/g, '').trim()); // removes commas, trims spaces, converts to number
      
      const d: Date = this.form.value.date; // Date from picker 
      const dateIso = formatDate(d, 'yyyy-MM-dd', 'en-CA'); // '2025-10-02' // Formats date to ISO string (YYYY-MM-DD)
      
      // Client-side guards that often trigger 400s on the server
      if (!category) { this.error = 'Enter a corrected category.'; return; }
      if (!vendor || vendor.length < 3) { this.error = 'Vendor is too short.'; return; }
      if (!description || description.length < 3) { this.error = 'Description is too short.'; return; }
      if (!dateIso) { this.error = 'Please provide a valid date (YYYY-MM-DD).'; return; }
      if (!isFinite(amountNum) || amountNum <= 0) { this.error = 'Amount must be a positive number.'; return; }

      if (!category) { this.error = 'Enter a corrected category.'; return; } // If category is empty, sets an error message and exits the function
      this.api.feedback({ vendor, description, date: dateIso, amount: amountNum, category }).subscribe({
        next: () => {
          this.form.reset(); // Resets the main form on successful feedback submission
          this.result = null; // Clears the prediction result
          this.correctionForm.reset(); // Resets the correction form on successful feedback submission
          alert('Thanks — your expense was recorded.')
        },
        error: (err) => { this.error = err?.error?.detail ?? 'Feedback failed.'; }
      });
    }

  }




