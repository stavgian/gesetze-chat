import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { environment } from '../../environments/environment';
import { Chat } from './chat';

describe('Chat', () => {
  let component: Chat;
  let fixture: ComponentFixture<Chat>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Chat],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Chat);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    await fixture.whenStable();
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('shows an error instead of calling the backend when the question is empty', () => {
    component.question = '   ';
    component.ask();

    expect(component.error()).toBeTruthy();
    httpMock.expectNone(`${environment.apiBaseUrl}/ask`);
  });

  it('stores the response and clears loading state on a successful ask', () => {
    component.question = 'Wann darf der Vermieter kündigen?';
    component.ask();

    expect(component.loading()).toBe(true);

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/ask`);
    expect(req.request.method).toBe('POST');
    req.flush({
      answer: null,
      sources: [{ file: 'bgb_mietrecht.md', section: '§ 573 BGB', chunk: 'text', score: 0.9 }],
      mode: 'retrieval_only',
    });

    expect(component.loading()).toBe(false);
    expect(component.result()?.mode).toBe('retrieval_only');
    expect(component.result()?.sources.length).toBe(1);
  });
});
