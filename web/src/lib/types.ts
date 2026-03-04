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

export interface GraphNode {
	id: string;
	message_count: number;
	degree_centrality: number;
	betweenness_centrality: number;
	closeness_centrality: number;
}

export interface GraphEdge {
	source: string;
	target: string;
	weight: number;
}

export interface GraphData {
	nodes: GraphNode[];
	edges: GraphEdge[];
}

export interface UploadResponse {
	messages: Message[];
	stats: ParseStats;
	graph: GraphData;
}
