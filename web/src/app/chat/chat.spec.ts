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

  it('shows a form error instead of calling the backend when the question is empty', () => {
    component.question = '   ';
    component.ask();

    expect(component.formError()).toBeTruthy();
    expect(component.messages().length).toBe(0);
    httpMock.expectNone(`${environment.apiBaseUrl}/ask`);
  });

  it('appends a message and clears loading state on a successful ask', () => {
    component.question = 'Wann darf der Vermieter kündigen?';
    component.ask();

    expect(component.messages().length).toBe(1);
    expect(component.messages()[0].loading).toBe(true);

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/ask`);
    expect(req.request.method).toBe('POST');
    req.flush({
      answer: null,
      sources: [{ file: 'bgb_mietrecht.md', section: '§ 573 BGB', chunk: 'text', score: 0.9 }],
      mode: 'retrieval_only',
    });

    expect(component.messages()[0].loading).toBe(false);
    expect(component.messages()[0].result?.mode).toBe('retrieval_only');
    expect(component.messages()[0].result?.sources.length).toBe(1);
  });

  it('records an error on the message when the backend request fails', () => {
    component.question = 'Wann darf der Vermieter kündigen?';
    component.ask();

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/ask`);
    req.error(new ProgressEvent('error'));

    expect(component.messages()[0].loading).toBe(false);
    expect(component.messages()[0].error).toBeTruthy();
  });
});
