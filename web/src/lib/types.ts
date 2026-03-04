export interface Message {
	timestamp: string;
	sender: string;
	body: string;
	line_number: number;
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
}

export interface UploadResponse {
	messages: Message[];
	stats: ParseStats;
}
