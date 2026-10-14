import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
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
  private readonly http = inject(HttpClient);

  ask(question: string): Observable<AskResponse> {
    return this.http.post<AskResponse>(`${environment.apiBaseUrl}/ask`, { question });
  }
}
