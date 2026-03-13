<script lang="ts">
	import type { NerResult } from '$lib/types';
	import { filterState, selectEntity } from '$lib/selection.svelte';

	let { ner }: { ner: NerResult } = $props();

	const LABELS: Record<string, { icon: string; color: string; name: string }> = {
		PERSON:       { icon: '👤', color: '#f472b6', name: 'Person' },
		ORG:          { icon: '🏢', color: '#c084fc', name: 'Organization' },
		LOCATION:     { icon: '📍', color: '#2dd4bf', name: 'Location' },
		PHONE:        { icon: '📞', color: '#34d399', name: 'Phone' },
		EMAIL:        { icon: '✉️', color: '#4f8ff7', name: 'Email' },
		URL:          { icon: '🔗', color: '#a78bfa', name: 'Link' },
		MONEY:        { icon: '💰', color: '#fbbf24', name: 'Money' },
		CRYPTO_WALLET:{ icon: '🪙', color: '#fb923c', name: 'Crypto' },
		COORDINATES:  { icon: '🌐', color: '#818cf8', name: 'Coords' },
		DATE:         { icon: '📅', color: '#38bdf8', name: 'Date' },
	};

	function lbl(key: string) {
		return LABELS[key] ?? { icon: '•', color: '#888', name: key };
	}

	let activeFilter = $state<string | null>(null);

	let filtered = $derived.by(() => {
		let ents = ner.unique_entities;
		const sel = filterState.selection;

		if (sel.kind === 'person') {
			ents = ents.filter((e) => e.senders.includes(sel.sender));
		}

		// label type chip filter
		if (activeFilter) {
			ents = ents.filter((e) => e.label === activeFilter);
		}

		return ents;
	});

	function handleEntityClick(entity: { text: string; label: string; senders: string[] }) {
		selectEntity(entity.text, entity.label, entity.senders);
	}

	function isActive(entity: { text: string; label: string }) {
		const sel = filterState.selection;
		return sel.kind === 'entity' && sel.text === entity.text && sel.label === entity.label;
	}
</script>

<div class="panel">
	<div class="panel-header">
		<span class="title">Key Details Found</span>
		<span class="meta">{ner.total_found} items</span>
	</div>

	{#if ner.total_found === 0}
		<div class="empty">No phone numbers, emails, or other details were found in the messages.</div>
	{:else}
		<div class="label-chips">
			<button
				class="chip"
				class:active={activeFilter === null}
				onclick={() => (activeFilter = null)}
			>
				All ({ner.total_found})
			</button>
			{#each Object.entries(ner.label_counts) as [label, count]}
				<button
					class="chip"
					class:active={activeFilter === label}
					style="--chip-color: {lbl(label).color}"
					onclick={() => (activeFilter = activeFilter === label ? null : label)}
				>
					{lbl(label).icon} {lbl(label).name} ({count})
				</button>
			{/each}
		</div>

		<div class="entity-list">
			{#each filtered as entity (entity.label + '|' + entity.text)}
				{@const cfg = lbl(entity.label)}
				<button
					class="entity-row"
					class:entity-active={isActive(entity)}
					onclick={() => handleEntityClick(entity)}
				>
					<span class="entity-badge" style="background: {cfg.color}20; color: {cfg.color}">
						{cfg.name}
					</span>
					<span class="entity-text">{entity.text}</span>
					<span class="entity-meta">
						{entity.count}x &middot; {entity.senders.join(', ')}
					</span>
				</button>
			{/each}
		</div>
	{/if}
</div>

<style>
	.panel {
		background: var(--bg-card);
		border-radius: var(--radius);
		overflow: hidden;
	}

	.panel-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.title {
		font-weight: 600;
		font-size: 0.88rem;
		color: var(--text-primary);
	}

	.meta {
		font-size: 0.78rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
	}

	.empty {
		padding: 2rem;
		text-align: center;
		color: var(--text-muted);
		font-size: 0.85rem;
	}

	.label-chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		padding: 0.6rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.chip {
		font-size: 0.72rem;
		padding: 0.25rem 0.6rem;
		border-radius: 9999px;
		border: 1px solid var(--border);
		background: var(--bg-secondary);
		color: var(--text-secondary);
		cursor: pointer;
		transition: all 0.15s;
	}

	.chip:hover {
		border-color: var(--chip-color, var(--accent));
		color: var(--text-primary);
	}

	.chip.active {
		background: var(--chip-color, var(--accent));
		color: #fff;
		border-color: transparent;
	}

	.entity-list {
		max-height: 320px;
		overflow-y: auto;
		padding: 0.4rem 0;
	}

	.entity-row {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.4rem 1rem;
		font-size: 0.8rem;
		width: 100%;
		background: none;
		border: none;
		border-left: 3px solid transparent;
		cursor: pointer;
		text-align: left;
	}

	.entity-row:hover {
		background: var(--bg-hover);
	}

	.entity-active {
		border-left-color: var(--accent);
		background: var(--bg-hover);
	}

	.entity-badge {
		font-size: 0.65rem;
		font-weight: 600;
		padding: 0.15rem 0.45rem;
		border-radius: 4px;
		white-space: nowrap;
		flex-shrink: 0;
	}

	.entity-text {
		color: var(--text-primary);
		font-family: var(--font-mono);
		font-size: 0.78rem;
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.entity-meta {
		color: var(--text-muted);
		font-size: 0.7rem;
		white-space: nowrap;
		flex-shrink: 0;
	}
</style>
