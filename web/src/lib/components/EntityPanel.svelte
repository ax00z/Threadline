<script lang="ts">
	import type { NerResult } from '$lib/types';

	let { ner }: { ner: NerResult } = $props();

	const LABEL_ICONS: Record<string, string> = {
		PERSON: '👤',
		ORG: '🏢',
		LOCATION: '📍',
		PHONE: '📞',
		EMAIL: '✉️',
		URL: '🔗',
		MONEY: '💰',
		CRYPTO_WALLET: '🪙',
		COORDINATES: '🌐',
		DATE: '📅'
	};

	const LABEL_COLORS: Record<string, string> = {
		PERSON: '#f472b6',
		ORG: '#c084fc',
		LOCATION: '#2dd4bf',
		PHONE: '#34d399',
		EMAIL: '#4f8ff7',
		URL: '#a78bfa',
		MONEY: '#fbbf24',
		CRYPTO_WALLET: '#fb923c',
		COORDINATES: '#818cf8',
		DATE: '#38bdf8'
	};

	const LABEL_NAMES: Record<string, string> = {
		PERSON: 'Person',
		ORG: 'Organization',
		LOCATION: 'Location',
		PHONE: 'Phone',
		EMAIL: 'Email',
		URL: 'Link',
		MONEY: 'Money',
		CRYPTO_WALLET: 'Crypto',
		COORDINATES: 'Coords',
		DATE: 'Date'
	};

	let activeFilter = $state<string | null>(null);

	let filtered = $derived(
		activeFilter
			? ner.unique_entities.filter((e) => e.label === activeFilter)
			: ner.unique_entities
	);
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
					style="--chip-color: {LABEL_COLORS[label] || '#888'}"
					onclick={() => (activeFilter = activeFilter === label ? null : label)}
				>
					{LABEL_ICONS[label] || '•'} {LABEL_NAMES[label] || label} ({count})
				</button>
			{/each}
		</div>

		<div class="entity-list">
			{#each filtered as entity (entity.text + entity.label)}
				<div class="entity-row">
					<span class="entity-badge" style="background: {LABEL_COLORS[entity.label] || '#555'}20; color: {LABEL_COLORS[entity.label] || '#888'}">
						{LABEL_NAMES[entity.label] || entity.label}
					</span>
					<span class="entity-text">{entity.text}</span>
					<span class="entity-meta">
						{entity.count}x &middot; {entity.senders.join(', ')}
					</span>
				</div>
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
	}

	.entity-row:hover {
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
