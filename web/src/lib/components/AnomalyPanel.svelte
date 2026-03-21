<script lang="ts">
	import type { Anomaly } from '$lib/types';
	import { filterState, selectAnomaly, clearSelection } from '$lib/selection.svelte';

	let { anomalies }: { anomalies: Anomaly[] } = $props();

	const KIND_META: Record<string, { label: string; color: string }> = {
		burst: { label: 'Burst', color: '#e5534b' },
		off_hours: { label: 'Off-Hours', color: '#c69026' },
		new_contact: { label: 'New Contact', color: '#2d7ff9' },
		keyword_cluster: { label: 'Keywords', color: '#b083f0' },
	};

	const SEV_COLORS: Record<string, string> = {
		high: '#e5534b',
		medium: '#c69026',
		low: '#2d7ff9',
	};

	type KindFilter = string | null;
	let activeKind = $state<KindFilter>(null);
	let collapsed = $state(false);

	let kindCounts = $derived.by(() => {
		const counts: Record<string, number> = {};
		for (const a of anomalies) {
			counts[a.kind] = (counts[a.kind] || 0) + 1;
		}
		return counts;
	});

	let visible = $derived.by(() => {
		if (!activeKind) return anomalies;
		return anomalies.filter((a) => a.kind === activeKind);
	});

	function isActive(a: Anomaly): boolean {
		const sel = filterState.selection;
		if (sel.kind !== 'anomaly') return false;
		const si = sel.indices;
		const mi = a.message_indices;
		if (si.length !== mi.length) return false;
		for (let i = 0; i < si.length; i++) {
			if (si[i] !== mi[i]) return false;
		}
		return true;
	}

	function handleClick(a: Anomaly) {
		if (isActive(a)) {
			clearSelection();
		} else {
			selectAnomaly(a.message_indices);
		}
	}

	function fmtTime(iso: string): string {
		const d = new Date(iso);
		return (
			d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
			' ' +
			d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
		);
	}
</script>

<div class="panel">
	<button class="panel-header" onclick={() => collapsed = !collapsed}>
		<span class="toggle-icon">{collapsed ? '▸' : '▾'}</span>
		<span class="panel-title">Anomalies</span>
		<span class="badge">{anomalies.length}</span>
	</button>

	{#if collapsed}
		<!-- collapsed -->
	{:else if anomalies.length > 0}
		<div class="chips">
			<button
				class="chip"
				class:active={activeKind === null}
				onclick={() => (activeKind = null)}
			>
				All {anomalies.length}
			</button>
			{#each Object.entries(kindCounts) as [kind, count]}
				{@const meta = KIND_META[kind] || { label: kind, color: '#888' }}
				<button
					class="chip"
					class:active={activeKind === kind}
					style="--chip-color: {meta.color}"
					onclick={() => (activeKind = activeKind === kind ? null : kind)}
				>
					{meta.label} {count}
				</button>
			{/each}
		</div>

		<div class="list">
			{#each visible as anomaly}
				{@const meta = KIND_META[anomaly.kind] || { label: anomaly.kind, color: '#888' }}
				<button
					class="anomaly-row"
					class:active={isActive(anomaly)}
					onclick={() => handleClick(anomaly)}
				>
					<span class="sev-dot" style="background: {SEV_COLORS[anomaly.severity] || '#888'}"></span>
					<span class="kind-badge" style="color: {meta.color}">{meta.label}</span>
					<span class="desc">{anomaly.description}</span>
					<span class="ts">{fmtTime(anomaly.timestamp)}</span>
				</button>
			{/each}
		</div>
	{:else}
		<div class="empty">No anomalies detected</div>
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
		background: none;
		border-top: none;
		border-left: none;
		border-right: none;
		cursor: pointer;
		width: 100%;
		text-align: left;
		color: inherit;
	}

	.panel-header:hover {
		background: var(--bg-hover);
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
		flex: 1;
	}

	.badge {
		background: var(--bg-secondary);
		color: var(--text-secondary);
		font-size: 0.72rem;
		padding: 0.15rem 0.5rem;
		border-radius: 9999px;
		font-family: var(--font-mono);
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		padding: 0.6rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.chip {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		color: var(--text-secondary);
		font-size: 0.72rem;
		padding: 0.2rem 0.6rem;
		cursor: pointer;
		transition: all 0.12s;
	}

	.chip:hover {
		border-color: var(--chip-color, var(--accent));
		color: var(--chip-color, var(--accent));
	}

	.chip.active {
		background: var(--chip-color, var(--accent));
		color: #fff;
		border-color: transparent;
	}

	.list {
		max-height: 320px;
		overflow-y: auto;
	}

	.anomaly-row {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		width: 100%;
		padding: 0.55rem 1rem;
		border: none;
		border-bottom: 1px solid var(--border);
		border-left: 3px solid transparent;
		background: none;
		color: var(--text-primary);
		font-size: 0.8rem;
		cursor: pointer;
		text-align: left;
		transition: all 0.1s;
	}

	.anomaly-row:hover {
		background: var(--bg-hover);
	}

	.anomaly-row.active {
		border-left-color: var(--accent);
		background: var(--accent-muted);
	}

	.sev-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.kind-badge {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		font-weight: 600;
		flex-shrink: 0;
		width: 80px;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}

	.desc {
		flex: 1;
		color: var(--text-secondary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		min-width: 0;
	}

	.ts {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--text-muted);
		flex-shrink: 0;
		white-space: nowrap;
	}

	.empty {
		padding: 1.5rem;
		text-align: center;
		color: var(--text-muted);
		font-size: 0.82rem;
	}
</style>
