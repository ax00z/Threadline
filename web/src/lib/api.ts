import type { UploadResponse } from './types';

export async function uploadFile(file: File): Promise<UploadResponse> {
	const form = new FormData();
	form.append('file', file);

	const res = await fetch('/api/upload', {
		method: 'POST',
		body: form
	});

	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || 'Upload failed');
	}

	return res.json();
}

export interface QueryResult {
	columns: string[];
	rows: (string | null)[][];
	row_count: number;
	error?: string;
}

export async function runQuery(sql: string): Promise<QueryResult> {
	const res = await fetch('/api/query', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ sql })
	});

	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || 'Query failed');
	}

	return res.json();
}
