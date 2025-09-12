import { ComponentFixture, TestBed } from '@angular/core/testing';

import { PredictComp } from './predict.comp';

describe('PredictComp', () => {
  let component: PredictComp;
  let fixture: ComponentFixture<PredictComp>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PredictComp]
    })
    .compileComponents();

    fixture = TestBed.createComponent(PredictComp);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
