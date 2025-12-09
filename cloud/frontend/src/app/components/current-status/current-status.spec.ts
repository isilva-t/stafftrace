import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CurrentStatus } from './current-status';

describe('CurrentStatus', () => {
  let component: CurrentStatus;
  let fixture: ComponentFixture<CurrentStatus>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CurrentStatus]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CurrentStatus);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
