<script lang="ts">
	import type { HeatmapData } from '$lib/types';

	let { heatmap }: { heatmap: HeatmapData } = $props();

	let maxVal = $derived.by(() => {
		let m = 0;
		for (const row of heatmap.matrix) {
			for (const v of row) {
				if (v > m) m = v;
			}
		}
		return m || 1;
	});

	function cellColor(val: number): string {
		if (val === 0) return 'var(--bg-secondary)';
		const intensity = val / maxVal;
		const r = Math.round(79 + (248 - 79) * intensity);
		const g = Math.round(143 + (113 - 143) * intensity);
		const b = Math.round(247 + (113 - 247) * intensity);
		return `rgb(${r}, ${g}, ${b})`;
	}

	function fmtHour(h: number): string {
		if (h === 0) return '12a';
		if (h < 12) return `${h}a`;
		if (h === 12) return '12p';
		return `${h - 12}p`;
	}

	let hoveredCell = $state<{ day: number; hour: number; count: number } | null>(null);
</script>

<div class="panel">
	<div class="panel-header">
		<span class="panel-title">Activity Heatmap</span>
		<span class="badge">peak: {heatmap.peak.day} {fmtHour(heatmap.peak.hour)} ({heatmap.peak.count})</span>
	</div>

	<div class="heatmap-wrap">
		{#if hoveredCell}
			<div class="tooltip">
				{heatmap.day_labels[hoveredCell.day]} {fmtHour(hoveredCell.hour)} — {hoveredCell.count} messages
			</div>
		{/if}

		<div class="grid">
			<div class="corner"></div>
			{#each Array(24) as _, h}
				<div class="hour-label">{h % 3 === 0 ? fmtHour(h) : ''}</div>
			{/each}

			{#each heatmap.matrix as row, d}
				<div class="day-label">{heatmap.day_labels[d]}</div>
				{#each row as val, h}
					<div
						class="cell"
						style="background: {cellColor(val)}"
						role="gridcell"
						onmouseenter={() => hoveredCell = { day: d, hour: h, count: val }}
						onmouseleave={() => hoveredCell = null}
					></div>
				{/each}
			{/each}
		</div>

		<div class="legend">
			<span class="legend-label">Less</span>
			{#each [0, 0.25, 0.5, 0.75, 1] as t}
				<div class="legend-cell" style="background: {cellColor(t * maxVal)}"></div>
			{/each}
			<span class="legend-label">More</span>
		</div>
	</div>
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

	.heatmap-wrap {
		padding: 1rem;
		position: relative;
	}

	.tooltip {
		position: absolute;
		top: 0.3rem;
		right: 1rem;
		font-size: 0.7rem;
		color: var(--text-secondary);
		font-family: var(--font-mono);
	}

	.grid {
		display: grid;
		grid-template-columns: 32px repeat(24, 1fr);
		gap: 2px;
	}

	.corner {
		width: 32px;
	}

	.hour-label {
		font-size: 0.58rem;
		color: var(--text-muted);
		text-align: center;
		font-family: var(--font-mono);
		height: 14px;
		line-height: 14px;
	}

	.day-label {
		font-size: 0.65rem;
		color: var(--text-muted);
		text-align: right;
		padding-right: 4px;
		line-height: 1;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		font-family: var(--font-mono);
	}

	.cell {
		aspect-ratio: 1;
		border-radius: 2px;
		min-height: 12px;
		transition: opacity 0.1s;
	}

	.cell:hover {
		opacity: 0.8;
		outline: 1px solid var(--text-secondary);
	}

	.legend {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		gap: 3px;
		margin-top: 0.6rem;
	}

	.legend-label {
		font-size: 0.6rem;
		color: var(--text-muted);
		padding: 0 4px;
	}

	.legend-cell {
		width: 12px;
		height: 12px;
		border-radius: 2px;
	}
</style>
