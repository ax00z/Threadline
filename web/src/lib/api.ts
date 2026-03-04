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
