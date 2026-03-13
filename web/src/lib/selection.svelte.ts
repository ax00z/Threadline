import type { SelectionMode } from './types';

// can't reassign exported $state in svelte 5, so wrap in an object
// components read store.selection and store.timeRange
const store = $state<{
	selection: SelectionMode;
	timeRange: { start: string; end: string } | null;
}>({
	selection: { kind: 'none' },
	timeRange: null,
});

// read-only accessors — these are reactive because they read $state props
export function getSelection(): SelectionMode {
	return store.selection;
}

export function getTimeRange(): { start: string; end: string } | null {
	return store.timeRange;
}

// convenience for components that want to bind to a derived
export { store as filterState };

export function selectPerson(sender: string) {
	if (store.selection.kind === 'person' && store.selection.sender === sender) {
		store.selection = { kind: 'none' };
	} else {
		store.selection = { kind: 'person', sender };
	}
}

export function selectEdge(source: string, target: string) {
	if (
		store.selection.kind === 'edge' &&
		store.selection.source === source &&
		store.selection.target === target
	) {
		store.selection = { kind: 'none' };
	} else {
		store.selection = { kind: 'edge', source, target };
	}
}

export function selectEntity(text: string, label: string, senders: string[]) {
	if (store.selection.kind === 'entity' && store.selection.text === text) {
		store.selection = { kind: 'none' };
	} else {
		store.selection = { kind: 'entity', text, label, senders };
	}
}

export function selectAnomaly(indices: number[]) {
	store.selection = { kind: 'anomaly', indices };
}

export function clearSelection() {
	store.selection = { kind: 'none' };
}

export function setTimeRange(start: string, end: string) {
	store.timeRange = { start, end };
}

export function clearTimeRange() {
	store.timeRange = null;
}

export function clearAll() {
	store.selection = { kind: 'none' };
	store.timeRange = null;
}
