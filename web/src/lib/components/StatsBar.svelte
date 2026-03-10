<script lang="ts">
	import type { ParseStats } from '$lib/types';

	let { stats }: { stats: ParseStats } = $props();

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
		<span class="label">Total Messages</span>
	</div>
	<div class="stat">
		<span class="value">{stats.unique_senders}</span>
		<span class="label">People</span>
	</div>
	<div class="stat">
		<span class="value">{fmtDate(stats.first_message)} &ndash; {fmtDate(stats.last_message)}</span>
		<span class="label">Time Span ({days} {days === 1 ? 'day' : 'days'})</span>
	</div>
	<div class="stat">
		<span class="value">{perDay.toLocaleString()}</span>
		<span class="label">Messages per Day</span>
	</div>
</div>

<style>
	.stats-bar {
		display: flex;
		flex-wrap: wrap;
		gap: 1px;
		background: var(--border);
		border-radius: var(--radius);
		overflow: hidden;
	}

	.stat {
		flex: 1 1 140px;
		background: var(--bg-card);
		padding: 1rem 1.2rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	.value {
		font-size: 1.1rem;
		font-weight: 600;
		color: var(--text-primary);
	}

	.label {
		font-size: 0.75rem;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
</style>
