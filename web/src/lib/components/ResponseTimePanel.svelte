<script lang="ts">
	import type { ResponseTimeData } from '$lib/types';

	let { responseTimes }: { responseTimes: ResponseTimeData } = $props();
	let collapsed = $state(false);

	let sortedSenders = $derived.by(() => {
		return Object.entries(responseTimes.per_sender)
			.sort((a, b) => a[1].avg_seconds - b[1].avg_seconds);
	});

	let maxAvg = $derived.by(() => {
		let m = 0;
		for (const [, s] of sortedSenders) {
			if (s.avg_seconds > m) m = s.avg_seconds;
		}
		return m || 1;
	});

	function fmtDuration(secs: number): string {
		if (secs < 60) return `${Math.round(secs)}s`;
		if (secs < 3600) return `${Math.round(secs / 60)}m`;
		return `${(secs / 3600).toFixed(1)}h`;
	}

	function barColor(secs: number): string {
		if (secs < 30) return '#57ab5a';
		if (secs < 120) return '#2d7ff9';
		if (secs < 600) return '#c69026';
		return '#e5534b';
	}
</script>

<div class="panel">
	<button class="panel-header" onclick={() => collapsed = !collapsed}>
		<span class="toggle-icon">{collapsed ? '▸' : '▾'}</span>
		<span class="panel-title">Response Times</span>
		{#if responseTimes.fastest}
			<span class="badge fastest">fastest: {responseTimes.fastest}</span>
		{/if}
	</button>

	{#if !collapsed && sortedSenders.length > 0}
		<div class="sender-list">
			{#each sortedSenders as [sender, stats]}
				<div class="sender-row">
					<span class="sender-name">{sender}</span>
					<div class="bar-area">
						<div
							class="bar"
							style="width: {(stats.avg_seconds / maxAvg) * 100}%; background: {barColor(stats.avg_seconds)}"
						></div>
					</div>
					<span class="stat avg">{fmtDuration(stats.avg_seconds)}</span>
					<span class="stat med">med {fmtDuration(stats.median_seconds)}</span>
					<span class="stat count">{stats.count}×</span>
				</div>
			{/each}
		</div>

		{#if responseTimes.pairs.length > 0}
			<div class="section-label">By pair</div>
			<div class="pair-list">
				{#each responseTimes.pairs.slice(0, 15) as p}
					<div class="pair-row">
						<span class="pair-names">{p.pair[0]} ↔ {p.pair[1]}</span>
						<span class="pair-avg">{fmtDuration(p.avg_seconds)}</span>
						<span class="pair-count">{p.count}×</span>
					</div>
				{/each}
			</div>
		{/if}
	{:else if !collapsed}
		<div class="empty">Not enough messages to compute response times</div>
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
		width: 100%;
		padding: 0.75rem 1rem;
		border: none;
		background: none;
		cursor: pointer;
		color: var(--text-primary);
	}

	.panel-header:hover { background: var(--bg-hover); }

	.toggle-icon {
		font-size: 0.7rem;
		color: var(--text-muted);
		width: 0.8rem;
	}

	.panel-title {
		font-weight: 600;
		font-size: 0.85rem;
		color: var(--text-primary);
	}

	.badge {
		background: var(--bg-secondary);
		color: var(--text-secondary);
		font-size: 0.68rem;
		padding: 0.15rem 0.5rem;
		border-radius: 9999px;
		font-family: var(--font-mono);
		margin-left: auto;
	}

	.badge.fastest {
		color: #57ab5a;
	}

	.sender-list {
		max-height: 260px;
		overflow-y: auto;
	}

	.sender-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.4rem 1rem;
		border-bottom: 1px solid var(--border);
	}

	.sender-name {
		width: 110px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 0.78rem;
		color: var(--text-secondary);
	}

	.bar-area {
		flex: 1;
		height: 6px;
		background: var(--bg-secondary);
		border-radius: 3px;
		overflow: hidden;
	}

	.bar {
		height: 100%;
		border-radius: 3px;
		transition: width 0.3s;
	}

	.stat {
		font-family: var(--font-mono);
		font-size: 0.68rem;
		color: var(--text-muted);
		white-space: nowrap;
	}

	.stat.avg {
		width: 36px;
		text-align: right;
		color: var(--text-secondary);
	}

	.stat.med {
		width: 52px;
	}

	.stat.count {
		width: 28px;
		text-align: right;
	}

	.section-label {
		padding: 0.5rem 1rem 0.25rem;
		font-size: 0.72rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 600;
		border-top: 1px solid var(--border);
	}

	.pair-list {
		max-height: 200px;
		overflow-y: auto;
	}

	.pair-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.35rem 1rem;
		border-bottom: 1px solid var(--border);
		font-size: 0.75rem;
	}

	.pair-names {
		flex: 1;
		color: var(--text-secondary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.pair-avg {
		font-family: var(--font-mono);
		font-size: 0.7rem;
		color: var(--text-secondary);
	}

	.pair-count {
		font-family: var(--font-mono);
		font-size: 0.68rem;
		color: var(--text-muted);
		width: 28px;
		text-align: right;
	}

	.empty {
		padding: 1.5rem;
		text-align: center;
		color: var(--text-muted);
		font-size: 0.82rem;
	}
</style>
