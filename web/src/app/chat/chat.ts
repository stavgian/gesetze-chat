import { FormsModule } from '@angular/forms';
import { Component, ElementRef, ViewChild, signal } from '@angular/core';

import { AskResponse, ChatService } from './chat.service';

export interface ChatMessage {
  question: string;
  result: AskResponse | null;
  error: string | null;
  loading: boolean;
}

@Component({
  selector: 'app-chat',
  imports: [FormsModule],
  templateUrl: './chat.html',
  styleUrl: './chat.scss',
})
export class Chat {
  question = '';
  readonly messages = signal<ChatMessage[]>([]);
  readonly formError = signal<string | null>(null);
  readonly expandedSources = signal<Set<string>>(new Set());

  @ViewChild('thread') private threadRef?: ElementRef<HTMLDivElement>;

  constructor(private readonly chatService: ChatService) {}

  get isLoading(): boolean {
    const messages = this.messages();
    return messages.length > 0 && messages[messages.length - 1].loading;
  }

  ask(): void {
    const question = this.question.trim();
    if (!question) {
      this.formError.set('Please enter a question.');
      return;
    }
    if (this.isLoading) {
      return;
    }

    this.formError.set(null);
    this.question = '';
    this.messages.update((messages) => [
      ...messages,
      { question, result: null, error: null, loading: true },
    ]);
    this.scrollToBottom();

    this.chatService.ask(question).subscribe({
      next: (response) => this.updateLastMessage({ result: response, loading: false }),
      error: () =>
        this.updateLastMessage({
          error: 'Could not reach the backend. Is the API running on the configured URL?',
          loading: false,
        }),
    });
  }

  toggleSource(key: string): void {
    const expanded = new Set(this.expandedSources());
    if (expanded.has(key)) {
      expanded.delete(key);
    } else {
      expanded.add(key);
    }
    this.expandedSources.set(expanded);
  }

  isExpanded(key: string): boolean {
    return this.expandedSources().has(key);
  }

  private updateLastMessage(patch: Partial<ChatMessage>): void {
    this.messages.update((messages) => {
      const updated = [...messages];
      const last = updated[updated.length - 1];
      updated[updated.length - 1] = { ...last, ...patch };
      return updated;
    });
    this.scrollToBottom();
  }

  // Runs after the DOM updates so the thread element has its new scrollHeight.
  private scrollToBottom(): void {
    setTimeout(() => {
      const el = this.threadRef?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    });
  }
}
