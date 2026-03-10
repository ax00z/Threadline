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
	pagerank: number;
	community: number;
}

export interface GraphEdge {
	source: string;
	target: string;
	weight: number;
}

export interface Community {
	id: number;
	members: string[];
	size: number;
	total_messages: number;
}

export interface GraphData {
	nodes: GraphNode[];
	edges: GraphEdge[];
	communities: Community[];
}

export interface NerEntity {
	text: string;
	label: string;
	count: number;
	senders: string[];
}

export interface NerResult {
	entities: Record<string, unknown>[];
	unique_entities: NerEntity[];
	label_counts: Record<string, number>;
	sender_entities: Record<string, Record<string, string[]>>;
	total_found: number;
}

export interface UploadResponse {
	messages: Message[];
	stats: ParseStats;
	graph: GraphData;
	ner: NerResult;
}
