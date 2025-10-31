import { Routes } from '@angular/router';
import { PredictComp } from './pages/predict.comp/predict.comp';

export const routes: Routes = [
    { path: '', redirectTo: 'predict', pathMatch: 'full' }, // Redirects the root path to /predict
    { path: 'predict', component: PredictComp } // Maps the /predict path to the PredictComp component 
];