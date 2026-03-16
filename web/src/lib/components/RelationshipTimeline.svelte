<script lang="ts">
	import type { PairwiseStats } from '$lib/types';
	import { filterState, selectEdge } from '$lib/selection.svelte';

	let { pairwise }: { pairwise: PairwiseStats[] } = $props();

	let sortBy = $state<'messages' | 'recent' | 'duration'>('messages');
	let collapsed = $state(false);

	let sorted = $derived.by(() => {
		const copy = [...pairwise];
		if (sortBy === 'messages') copy.sort((a, b) => b.message_count - a.message_count);
		else if (sortBy === 'recent') copy.sort((a, b) => b.last_contact.localeCompare(a.last_contact));
		else copy.sort((a, b) => b.duration_days - a.duration_days);
		return copy;
	});

	function isActive(p: PairwiseStats): boolean {
		const sel = filterState.selection;
		if (sel.kind !== 'edge') return false;
		const pair = new Set(p.pair);
		return pair.has(sel.source) && pair.has(sel.target);
	}

	function handleClick(p: PairwiseStats) {
		selectEdge(p.pair[0], p.pair[1]);
	}

	function fmtDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	// build sparkline data for a pair
	function sparklineBars(p: PairwiseStats): { heights: number[]; count: number } {
		const entries = Object.entries(p.daily_counts).sort(([a], [b]) => a.localeCompare(b));
		if (entries.length === 0) return { heights: [], count: 0 };

		// fill date gaps
		const startDate = new Date(entries[0][0]);
		const endDate = new Date(entries[entries.length - 1][0]);
		const dayMs = 86_400_000;
		const days: number[] = [];
		const dateMap = new Map(entries.map(([d, c]) => [d, c]));

		for (let d = new Date(startDate); d <= endDate; d = new Date(d.getTime() + dayMs)) {
			const key = d.toISOString().slice(0, 10);
			days.push(dateMap.get(key) || 0);
		}

		const max = Math.max(...days, 1);
		return {
			heights: days.map((v) => v / max),
			count: days.length,
		};
	}
</script>

<div class="panel">
	<div class="panel-header">
		<button class="toggle-btn" onclick={() => collapsed = !collapsed}>
			<span class="toggle-icon">{collapsed ? '▸' : '▾'}</span>
			<span class="panel-title">Relationships</span>
			<span class="badge">{pairwise.length}</span>
		</button>
		{#if !collapsed}
			<div class="sort-controls">
				<button class:active={sortBy === 'messages'} onclick={() => (sortBy = 'messages')}>Messages</button>
				<button class:active={sortBy === 'recent'} onclick={() => (sortBy = 'recent')}>Recent</button>
				<button class:active={sortBy === 'duration'} onclick={() => (sortBy = 'duration')}>Duration</button>
			</div>
		{/if}
	</div>

	{#if collapsed}
		<!-- collapsed -->
	{:else if pairwise.length > 0}
		<div class="list">
			{#each sorted as pair}
				{@const spark = sparklineBars(pair)}
				<button
					class="pair-row"
					class:active={isActive(pair)}
					onclick={() => handleClick(pair)}
				>
					<div class="pair-info">
						<span class="pair-label">{pair.pair[0]} ↔ {pair.pair[1]}</span>
						<span class="pair-meta">
							{pair.message_count} msgs · {pair.duration_days}d · {fmtDate(pair.first_contact)} – {fmtDate(pair.last_contact)}
						</span>
					</div>
					{#if spark.heights.length > 0}
						<svg class="sparkline" viewBox="0 0 {spark.count} 1" preserveAspectRatio="none">
							{#each spark.heights as h, i}
								<rect
									x={i}
									y={1 - h}
									width={0.8}
									height={Math.max(h, 0.05)}
									fill="var(--accent)"
									opacity={0.3 + h * 0.7}
								/>
							{/each}
						</svg>
					{/if}
				</button>
			{/each}
		</div>
	{:else}
		<div class="empty">No pairwise communication detected</div>
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
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.toggle-btn {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		background: none;
		border: none;
		cursor: pointer;
		color: inherit;
		padding: 0;
	}

	.toggle-btn:hover .panel-title {
		color: var(--accent);
	}

	.toggle-icon {
		font-size: 0.7rem;
		color: var(--text-muted);
		width: 0.8rem;
	}

	.panel-title {
		font-weight: 600;
		font-size: 0.85rem;
		color: var(--text-primary);
		transition: color 0.1s;
	}

	.badge {
		background: var(--bg-secondary);
		color: var(--text-secondary);
		font-size: 0.72rem;
		padding: 0.15rem 0.5rem;
		border-radius: 9999px;
		font-family: var(--font-mono);
	}

	.sort-controls {
		margin-left: auto;
		display: flex;
		gap: 0.25rem;
	}

	.sort-controls button {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text-muted);
		font-size: 0.68rem;
		padding: 0.15rem 0.5rem;
		cursor: pointer;
		transition: all 0.1s;
	}

	.sort-controls button:hover {
		color: var(--text-secondary);
	}

	.sort-controls button.active {
		background: var(--accent);
		color: #fff;
		border-color: transparent;
	}

	.list {
		max-height: 360px;
		overflow-y: auto;
	}

	.pair-row {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		width: 100%;
		padding: 0.6rem 1rem;
		border: none;
		border-bottom: 1px solid var(--border);
		border-left: 3px solid transparent;
		background: none;
		color: var(--text-primary);
		cursor: pointer;
		text-align: left;
		transition: all 0.1s;
	}

	.pair-row:hover {
		background: var(--bg-hover);
	}

	.pair-row.active {
		border-left-color: var(--accent);
		background: var(--accent-muted);
	}

	.pair-info {
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
		min-width: 0;
		flex: 1;
	}

	.pair-label {
		font-size: 0.82rem;
		font-weight: 500;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.pair-meta {
		font-size: 0.7rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
		white-space: nowrap;
	}

	.sparkline {
		width: 120px;
		height: 22px;
		flex-shrink: 0;
	}

	.empty {
		padding: 1.5rem;
		text-align: center;
		color: var(--text-muted);
		font-size: 0.82rem;
	}
</style>
