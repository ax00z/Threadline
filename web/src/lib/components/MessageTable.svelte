<script lang="ts">
	import type { Message } from '$lib/types';
	import { filterState, selectPerson, clearSelection } from '$lib/selection.svelte';

	let {
		messages,
		senderColors
	}: {
		messages: Message[];
		senderColors: Map<string, string>;
	} = $props();

	let search = $state('');
	let collapsed = $state(false);
	const PAGE_SIZE = 200;
	let page = $state(0);

	let filtered = $derived.by(() => {
		let msgs = messages;
		const sel = filterState.selection;
		const tr = filterState.timeRange;

		if (tr) {
			msgs = msgs.filter((m) => m.timestamp >= tr.start && m.timestamp <= tr.end);
		}

		if (sel.kind === 'person') {
			msgs = msgs.filter((m) => m.sender === sel.sender);
		} else if (sel.kind === 'edge') {
			msgs = msgs.filter(
				(m) => m.sender === sel.source || m.sender === sel.target
			);
		} else if (sel.kind === 'entity') {
			msgs = msgs.filter((m) => sel.senders.includes(m.sender));
		} else if (sel.kind === 'anomaly') {
			const idxSet = new Set(sel.indices);
			msgs = msgs.filter((m) => m.chain_index !== undefined && idxSet.has(m.chain_index));
		}

		// text search
		if (search) {
			const q = search.toLowerCase();
			msgs = msgs.filter(
				(m) =>
					m.body.toLowerCase().includes(q) ||
					m.sender.toLowerCase().includes(q)
			);
		}

		page = 0; // reset page when filters change
		return msgs;
	});

	let paged = $derived(filtered.slice(0, (page + 1) * PAGE_SIZE));
	let hasMore = $derived(paged.length < filtered.length);

	// label for the active filter
	let filterLabel = $derived.by(() => {
		const sel = filterState.selection;
		if (sel.kind === 'person') return sel.sender;
		if (sel.kind === 'edge') return `${sel.source} ↔ ${sel.target}`;
		if (sel.kind === 'entity') return `${sel.label}: ${sel.text}`;
		if (sel.kind === 'anomaly') return `Anomaly (${sel.indices.length} messages)`;
		return '';
	});

	function fmtTime(iso: string): string {
		const d = new Date(iso);
		return (
			d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
			' ' +
			d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
		);
	}
</script>

<div class="table-wrap" class:collapsed>
	<button class="collapse-header" onclick={() => collapsed = !collapsed}>
		<span class="collapse-icon">{collapsed ? '▸' : '▾'}</span>
		<span class="collapse-title">Messages</span>
		<span class="collapse-count">{filtered.length.toLocaleString()}</span>
	</button>

	{#if !collapsed}
		{#if filterLabel}
			<div class="filter-bar">
				<span class="filter-label">Showing: {filterLabel}</span>
				<button class="filter-clear" onclick={() => clearSelection()}>×</button>
			</div>
		{/if}

		<div class="search-bar">
			<input type="text" bind:value={search} placeholder="Search messages or senders…" />
		</div>

		<div class="scroll-area">
			{#each paged as msg (msg.line_number)}
				<div class="row" style="border-left-color: {senderColors.get(msg.sender) || '#555'}">
					<span class="ts">{fmtTime(msg.timestamp)}</span>
					<button
						class="sender"
						style="color: {senderColors.get(msg.sender) || '#aaa'}"
						onclick={() => selectPerson(msg.sender)}
					>
						{msg.sender}
					</button>
					<span class="body">{msg.body}</span>
				</div>
			{/each}
			{#if hasMore}
				<button class="load-more" onclick={() => page++}>
					Load more ({filtered.length - paged.length} remaining)
				</button>
			{/if}
		</div>
	{/if}
</div>

<style>
	.table-wrap {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--bg-card);
		border-radius: var(--radius);
		overflow: hidden;
	}

	.table-wrap.collapsed {
		height: auto;
	}

	.collapse-header {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.6rem 1rem;
		background: none;
		border: none;
		border-bottom: 1px solid var(--border);
		cursor: pointer;
		color: var(--text-primary);
		width: 100%;
		text-align: left;
	}

	.collapse-header:hover {
		background: var(--bg-hover);
	}

	.collapse-icon {
		font-size: 0.7rem;
		color: var(--text-muted);
		width: 0.8rem;
	}

	.collapse-title {
		font-weight: 600;
		font-size: 0.82rem;
	}

	.collapse-count {
		font-size: 0.72rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
		margin-left: auto;
	}

	.filter-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.4rem 1rem;
		background: var(--accent);
		color: #fff;
		font-size: 0.78rem;
		font-weight: 500;
	}

	.filter-label {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.filter-clear {
		background: none;
		border: none;
		color: #fff;
		font-size: 1rem;
		cursor: pointer;
		padding: 0 0.3rem;
		opacity: 0.7;
		line-height: 1;
	}

	.filter-clear:hover {
		opacity: 1;
	}

	.search-bar {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.search-bar input {
		flex: 1;
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		padding: 0.5rem 0.75rem;
		color: var(--text-primary);
		font-size: 0.85rem;
		outline: none;
	}

	.search-bar input:focus {
		border-color: var(--accent);
	}

	.search-bar input::placeholder {
		color: var(--text-muted);
	}

	.count {
		font-size: 0.75rem;
		color: var(--text-secondary);
		white-space: nowrap;
	}

	.scroll-area {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
		min-height: 0;
	}

	.row {
		display: flex;
		gap: 0.75rem;
		padding: 0.5rem 1rem;
		border-left: 3px solid transparent;
		border-bottom: 1px solid var(--border);
		font-size: 0.83rem;
		align-items: baseline;
	}

	.row:hover {
		background: var(--bg-hover);
	}

	.ts {
		color: var(--text-muted);
		font-family: var(--font-mono);
		font-size: 0.75rem;
		white-space: nowrap;
		flex-shrink: 0;
	}

	.sender {
		font-weight: 600;
		font-size: 0.8rem;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		flex-shrink: 0;
		width: 120px;
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		text-align: left;
	}

	.sender:hover {
		text-decoration: underline;
	}

	.body {
		color: var(--text-primary);
		white-space: pre-wrap;
		word-break: break-word;
		flex: 1;
		min-width: 0;
	}

	.load-more {
		display: block;
		width: 100%;
		padding: 0.6rem;
		background: var(--bg-secondary);
		border: none;
		border-top: 1px solid var(--border);
		color: var(--accent);
		font-size: 0.8rem;
		cursor: pointer;
		text-align: center;
	}

	.load-more:hover {
		background: var(--bg-hover);
	}
</style>
