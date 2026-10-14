import { FormsModule } from '@angular/forms';
import { Component, signal } from '@angular/core';

import { AskResponse, ChatService } from './chat.service';

@Component({
  selector: 'app-chat',
  imports: [FormsModule],
  templateUrl: './chat.html',
  styleUrl: './chat.scss',
})
export class Chat {
  question = '';
  readonly loading = signal(false);
  readonly result = signal<AskResponse | null>(null);
  readonly error = signal<string | null>(null);
  readonly expandedSources = signal<Set<number>>(new Set());

  constructor(private readonly chatService: ChatService) {}

  ask(): void {
    const question = this.question.trim();
    if (!question) {
      this.error.set('Please enter a question.');
      return;
    }

    this.loading.set(true);
    this.error.set(null);
    this.result.set(null);
    this.expandedSources.set(new Set());

    this.chatService.ask(question).subscribe({
      next: (response) => {
        this.result.set(response);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Could not reach the backend. Is the API running on the configured URL?');
        this.loading.set(false);
      },
    });
  }

  toggleSource(index: number): void {
    const expanded = new Set(this.expandedSources());
    if (expanded.has(index)) {
      expanded.delete(index);
    } else {
      expanded.add(index);
    }
    this.expandedSources.set(expanded);
  }

  isExpanded(index: number): boolean {
    return this.expandedSources().has(index);
  }
}
