<script lang="ts">
	import type { ParseStats, ChainResult } from '$lib/types';

	let { stats, chain }: { stats: ParseStats; chain: ChainResult } = $props();

	function fmtDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	let days = $derived(
		Math.max(
			1,
			Math.ceil(
				(new Date(stats.last_message).getTime() - new Date(stats.first_message).getTime()) /
					86_400_000
			)
		)
	);

	let perDay = $derived(Math.round(stats.total_messages / days));
</script>

<div class="stats-bar">
	<div class="stat">
		<span class="value">{stats.total_messages.toLocaleString()}</span>
		<span class="label">messages</span>
	</div>
	<div class="stat">
		<span class="value">{stats.unique_senders}</span>
		<span class="label">people</span>
	</div>
	<div class="stat">
		<span class="value">{fmtDate(stats.first_message)} &ndash; {fmtDate(stats.last_message)}</span>
		<span class="label">{days} {days === 1 ? 'day' : 'days'}</span>
	</div>
	<div class="stat">
		<span class="value">{perDay.toLocaleString()}/day</span>
		<span class="label">avg rate</span>
	</div>
	<div class="stat">
		{#if chain.valid}
			<span class="value chain-ok">INTACT</span>
			<span class="label">chain ({chain.checked})</span>
		{:else}
			<span class="value chain-fail">BROKEN @ #{chain.broken_at}</span>
			<span class="label">chain integrity</span>
		{/if}
	</div>
</div>

<style>
	.stats-bar {
		display: flex;
		flex-wrap: wrap;
		gap: 1px;
		background: var(--border-subtle);
	}

	.stat {
		flex: 1 1 120px;
		background: var(--bg-card);
		padding: 0.6rem 0.8rem;
		display: flex;
		flex-direction: column;
		gap: 0.15rem;
	}

	.value {
		font-size: 0.9rem;
		font-weight: 600;
		font-family: var(--font-mono);
		color: var(--text-primary);
	}

	.label {
		font-size: 0.65rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.1em;
		font-family: var(--font-mono);
	}

	.chain-ok {
		color: var(--success);
	}

	.chain-fail {
		color: var(--danger);
	}
</style>
