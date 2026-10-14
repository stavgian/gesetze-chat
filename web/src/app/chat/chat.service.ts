import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export interface Source {
  file: string;
  section: string;
  chunk: string;
  score: number;
}

export interface AskResponse {
  answer: string | null;
  sources: Source[];
  mode: 'full' | 'retrieval_only';
}

@Injectable({ providedIn: 'root' })
export class ChatService {
  constructor(private readonly http: HttpClient) {}

  ask(question: string): Observable<AskResponse> {
    return this.http.post<AskResponse>(`${environment.apiBaseUrl}/ask`, { question });
  }
}
