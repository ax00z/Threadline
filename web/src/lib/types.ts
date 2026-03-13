export interface Message {
	timestamp: string;
	sender: string;
	body: string;
	line_number: number;
	source_format: string;
	entities: Record<string, unknown>[];
	chain_hash?: string;
	previous_hash?: string;
	chain_index?: number;
}

export interface ChainResult {
	valid: boolean;
	checked: number;
	broken_at: number | null;
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

export interface Anomaly {
	kind: 'burst' | 'off_hours' | 'new_contact' | 'keyword_cluster';
	severity: 'high' | 'medium' | 'low';
	timestamp: string;
	description: string;
	message_indices: number[];
	actors: string[];
}

export interface PairwiseStats {
	pair: [string, string];
	first_contact: string;
	last_contact: string;
	message_count: number;
	duration_days: number;
	daily_counts: Record<string, number>;
}

export interface UploadResponse {
	messages: Message[];
	stats: ParseStats;
	graph: GraphData;
	ner: NerResult;
	chain: ChainResult;
	anomalies: Anomaly[];
	pairwise: PairwiseStats[];
}

export type SelectionMode =
	| { kind: 'none' }
	| { kind: 'person'; sender: string }
	| { kind: 'edge'; source: string; target: string }
	| { kind: 'entity'; text: string; label: string; senders: string[] }
	| { kind: 'anomaly'; indices: number[] };
