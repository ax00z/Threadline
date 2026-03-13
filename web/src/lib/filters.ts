import type { Message, SelectionMode } from './types';

export function filterMessages(
	messages: Message[],
	selection: SelectionMode,
	timeRange: { start: string; end: string } | null
): Message[] {
	let msgs = messages;

	if (timeRange) {
		msgs = msgs.filter((m) => m.timestamp >= timeRange.start && m.timestamp <= timeRange.end);
	}

	if (selection.kind === 'person') {
		msgs = msgs.filter((m) => m.sender === selection.sender);
	} else if (selection.kind === 'edge') {
		msgs = msgs.filter((m) => m.sender === selection.source || m.sender === selection.target);
	} else if (selection.kind === 'entity') {
		msgs = msgs.filter((m) => selection.senders.includes(m.sender));
	} else if (selection.kind === 'anomaly') {
		const idxSet = new Set(selection.indices);
		msgs = msgs.filter((m) => m.chain_index !== undefined && idxSet.has(m.chain_index));
	}

	return msgs;
}
