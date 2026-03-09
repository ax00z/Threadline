export const PALETTE = [
	'#4f8ff7',
	'#34d399',
	'#f87171',
	'#fbbf24',
	'#a78bfa',
	'#f472b6',
	'#38bdf8',
	'#fb923c',
	'#4ade80',
	'#e879f9'
];

export function buildSenderColorMap(senders: string[]): Map<string, string> {
	const map = new Map<string, string>();
	senders.forEach((s, i) => map.set(s, PALETTE[i % PALETTE.length]));
	return map;
}

export function communityColor(communityId: number): string {
	return PALETTE[communityId % PALETTE.length];
}
