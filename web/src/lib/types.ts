export interface Message {
	timestamp: string;
	sender: string;
	body: string;
	line_number: number;
	source_format: string;
	entities: Record<string, unknown>[];
}

export interface SenderBreakdown {
	[sender: string]: number;
}

export interface ParseStats {
	total_messages: number;
	unique_senders: number;
	senders: SenderBreakdown;
	first_message: string;
	last_message: string;
	source_format: string;
}

export interface UploadResponse {
	messages: Message[];
	stats: ParseStats;
}
