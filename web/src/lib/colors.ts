// Palantir-inspired muted intelligence palette
export const PALETTE = [
	'#2d7ff9',
	'#00b4d8',
	'#e5534b',
	'#c69026',
	'#b083f0',
	'#e07ab5',
	'#56b6c2',
	'#d49e6a',
	'#57ab5a',
	'#986ee2',
];

// Graph palette — muted but distinct, Palantir-style
export const GRAPH_PALETTE = [
	'#5b9bd5',
	'#d4726a',
	'#8fbc8f',
	'#c4a35a',
	'#9a8ec2',
	'#d48f6a',
	'#6bb5b5',
	'#c27a9a',
	'#7aab7a',
	'#7a9ec2',
];

export function buildSenderColorMap(senders: string[]): Map<string, string> {
	const map = new Map<string, string>();
	senders.forEach((s, i) => map.set(s, PALETTE[i % PALETTE.length]));
	return map;
}

export function communityColor(communityId: number): string {
	return GRAPH_PALETTE[communityId % GRAPH_PALETTE.length];
}

/** Assign each node a unique color from the graph palette by index. */
export function nodeColor(index: number): string {
	return GRAPH_PALETTE[index % GRAPH_PALETTE.length];
}
