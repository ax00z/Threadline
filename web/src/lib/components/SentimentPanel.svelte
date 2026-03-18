<script lang="ts">
	import type { SentimentResult } from '$lib/types';

	let { sentiment }: { sentiment: SentimentResult } = $props();
	let collapsed = $state(false);

	let sortedSenders = $derived.by(() => {
		return Object.entries(sentiment.per_sender)
			.toSorted((a, b) => a[1].compound - b[1].compound);
	});

	function barWidth(val: number): string {
		return `${Math.abs(val) * 100}%`;
	}

	function sentimentColor(compound: number): string {
		if (compound >= 0.05) return '#57ab5a';
		if (compound <= -0.05) return '#e5534b';
		return '#768390';
	}

	function sentimentLabel(compound: number): string {
		if (compound >= 0.05) return 'positive';
		if (compound <= -0.05) return 'negative';
		return 'neutral';
	}

	function fmtTime(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) +
			' ' + d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
	}
</script>

<div class="panel">
	<button class="panel-header" onclick={() => collapsed = !collapsed}>
		<span class="toggle-icon">{collapsed ? '▸' : '▾'}</span>
		<span class="panel-title">Sentiment Analysis</span>
		{#if !sentiment.available}
			<span class="badge warn">install vaderSentiment</span>
		{/if}
	</button>

	{#if !collapsed && sentiment.available}
		<div class="overall">
			<div class="overall-score" style="color: {sentimentColor(sentiment.overall.compound)}">
				{sentiment.overall.compound >= 0 ? '+' : ''}{sentiment.overall.compound.toFixed(3)}
			</div>
			<div class="overall-label">{sentimentLabel(sentiment.overall.compound)} overall tone</div>
			<div class="overall-bars">
				<div class="bar-row">
					<span class="bar-label">Positive (pos)</span>
					<div class="bar-track"><div class="bar-fill pos" style="width: {sentiment.overall.positive * 100}%"></div></div>
					<span class="bar-val">{(sentiment.overall.positive * 100).toFixed(1)}%</span>
				</div>
				<div class="bar-row">
					<span class="bar-label">Negative (neg)</span>
					<div class="bar-track"><div class="bar-fill neg" style="width: {sentiment.overall.negative * 100}%"></div></div>
					<span class="bar-val">{(sentiment.overall.negative * 100).toFixed(1)}%</span>
				</div>
				<div class="bar-row">
					<span class="bar-label">Neutral (neu)</span>
					<div class="bar-track"><div class="bar-fill neu" style="width: {sentiment.overall.neutral * 100}%"></div></div>
					<span class="bar-val">{(sentiment.overall.neutral * 100).toFixed(1)}%</span>
				</div>
			</div>
		</div>

		<div class="section-label">Per sender</div>
		<div class="sender-list">
			{#each sortedSenders as [sender, stats]}
				<div class="sender-row">
					<span class="sender-name">{sender}</span>
					<span class="sender-score" style="color: {sentimentColor(stats.compound)}">
						{stats.compound >= 0 ? '+' : ''}{stats.compound.toFixed(3)}
					</span>
					<div class="sender-bar-track">
						<div class="sender-bar" style="width: {barWidth(stats.compound)}; background: {sentimentColor(stats.compound)}"></div>
					</div>
				</div>
			{/each}
		</div>

		{#if sentiment.shifts.length > 0}
			<div class="section-label">Mood shifts ({sentiment.shifts.length})</div>
			<div class="shifts-list">
				{#each sentiment.shifts.slice(0, 20) as shift}
					<div class="shift-row">
						<span class="shift-sender">{shift.sender}</span>
						<span class="shift-desc">{shift.description}</span>
						<span class="shift-ts">{fmtTime(shift.timestamp)}</span>
					</div>
				{/each}
			</div>
		{/if}

		{#if sentiment.extremes.most_positive}
			<div class="section-label">Extremes</div>
			<div class="extremes">
				<div class="extreme-card">
					<span class="extreme-label pos-text">Most positive</span>
					<span class="extreme-sender">{sentiment.extremes.most_positive.sender}</span>
					<p class="extreme-body">"{sentiment.extremes.most_positive.body}"</p>
				</div>
				{#if sentiment.extremes.most_negative}
					<div class="extreme-card">
						<span class="extreme-label neg-text">Most negative</span>
						<span class="extreme-sender">{sentiment.extremes.most_negative.sender}</span>
						<p class="extreme-body">"{sentiment.extremes.most_negative.body}"</p>
					</div>
				{/if}
			</div>
		{/if}
	{:else if !collapsed}
		<div class="empty">Install vaderSentiment for sentiment analysis</div>
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

	.badge.warn {
		background: #c69026;
		color: #000;
		font-size: 0.65rem;
		padding: 0.1rem 0.45rem;
		border-radius: 9999px;
	}

	.overall {
		padding: 1rem;
		text-align: center;
		border-bottom: 1px solid var(--border);
	}

	.overall-score {
		font-size: 1.6rem;
		font-weight: 700;
		font-family: var(--font-mono);
	}

	.overall-label {
		font-size: 0.75rem;
		color: var(--text-muted);
		margin-bottom: 0.75rem;
	}

	.overall-bars {
		max-width: 280px;
		margin: 0 auto;
	}

	.bar-row {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		margin-bottom: 0.3rem;
	}

	.bar-label {
		font-size: 0.68rem;
		color: var(--text-muted);
		width: 90px;
		text-align: right;
		font-family: var(--font-mono);
	}

	.bar-track {
		flex: 1;
		height: 6px;
		background: var(--bg-secondary);
		border-radius: 3px;
		overflow: hidden;
	}

	.bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 0.3s;
	}

	.bar-fill.pos { background: #57ab5a; }
	.bar-fill.neg { background: #e5534b; }
	.bar-fill.neu { background: #768390; }

	.bar-val {
		font-size: 0.65rem;
		color: var(--text-muted);
		width: 36px;
		font-family: var(--font-mono);
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

	.sender-list {
		max-height: 220px;
		overflow-y: auto;
	}

	.sender-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.35rem 1rem;
		font-size: 0.78rem;
	}

	.sender-name {
		width: 120px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--text-secondary);
	}

	.sender-score {
		font-family: var(--font-mono);
		font-size: 0.72rem;
		width: 52px;
		text-align: right;
	}

	.sender-bar-track {
		flex: 1;
		height: 4px;
		background: var(--bg-secondary);
		border-radius: 2px;
		overflow: hidden;
	}

	.sender-bar {
		height: 100%;
		border-radius: 2px;
	}

	.shifts-list {
		max-height: 180px;
		overflow-y: auto;
	}

	.shift-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.35rem 1rem;
		font-size: 0.75rem;
		border-bottom: 1px solid var(--border);
	}

	.shift-sender {
		color: var(--text-secondary);
		width: 80px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.shift-desc {
		flex: 1;
		color: var(--text-muted);
	}

	.shift-ts {
		font-family: var(--font-mono);
		font-size: 0.68rem;
		color: var(--text-muted);
		white-space: nowrap;
	}

	.extremes {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 0.5rem;
		padding: 0.5rem 1rem 1rem;
	}

	.extreme-card {
		background: var(--bg-secondary);
		border-radius: var(--radius-sm);
		padding: 0.6rem;
	}

	.extreme-label {
		font-size: 0.65rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}

	.pos-text { color: #57ab5a; }
	.neg-text { color: #e5534b; }

	.extreme-sender {
		font-size: 0.72rem;
		color: var(--text-secondary);
		margin-left: 0.5rem;
	}

	.extreme-body {
		font-size: 0.72rem;
		color: var(--text-muted);
		margin-top: 0.3rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.empty {
		padding: 1.5rem;
		text-align: center;
		color: var(--text-muted);
		font-size: 0.82rem;
	}
</style>
