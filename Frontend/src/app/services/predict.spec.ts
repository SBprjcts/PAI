import { TestBed } from '@angular/core/testing';

import { Predict } from './predict';

describe('Predict', () => {
  let service: Predict;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(Predict);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
