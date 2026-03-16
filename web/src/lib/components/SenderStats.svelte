<script lang="ts">
	import { onMount } from 'svelte';
	import type { SenderBreakdown } from '$lib/types';
	import { buildSenderColorMap } from '$lib/colors';
	import { filterState, selectPerson } from '$lib/selection.svelte';
	import {
		Chart,
		BarController,
		CategoryScale,
		LinearScale,
		BarElement,
		Tooltip
	} from 'chart.js';

	Chart.register(BarController, CategoryScale, LinearScale, BarElement, Tooltip);

	let { senders }: { senders: SenderBreakdown } = $props();

	let canvas: HTMLCanvasElement;
	let chart: Chart | undefined;
	let senderLabels: string[] = [];
	let baseColors: string[] = [];
	let collapsed = $state(false);

	onMount(() => {
		const sorted = Object.entries(senders).sort((a, b) => b[1] - a[1]);
		senderLabels = sorted.map(([name]) => name);
		const senderValues = sorted.map(([, count]) => count);
		const colorMap = buildSenderColorMap(senderLabels);
		baseColors = senderLabels.map((l) => colorMap.get(l) || '#555');

		if (senderLabels.length === 0) return;

		requestAnimationFrame(() => {
			if (collapsed) return;
			chart = new Chart(canvas, {
				type: 'bar',
				data: {
					labels: senderLabels,
					datasets: [{ data: senderValues, backgroundColor: [...baseColors], borderRadius: 3 }]
				},
				options: {
					indexAxis: 'y',
					responsive: true,
					maintainAspectRatio: false,
					onClick(_e, elements) {
						if (elements.length > 0) {
							const name = senderLabels[elements[0].index];
							selectPerson(name);
						}
					},
					plugins: {
						legend: { display: false },
						tooltip: {
							callbacks: {
								label: (ctx: any) => `${ctx.raw.toLocaleString()} messages`
							}
						}
					},
					scales: {
						x: { grid: { color: '#1b2535' }, ticks: { color: '#768390' } },
						y: { grid: { display: false }, ticks: { color: '#cdd9e5', font: { size: 11 } } }
					}
				}
			});
		});

		return () => chart?.destroy();
	});

	$effect(() => {
		if (!chart || !chart.data.datasets[0]) return;
		const sel = filterState.selection;
		const ds = chart.data.datasets[0];
		if (sel.kind === 'person') {
			ds.backgroundColor = senderLabels.map((name, i) =>
				name === sel.sender ? baseColors[i] : baseColors[i] + '30'
			);
		} else {
			ds.backgroundColor = [...baseColors];
		}
		chart.update('none');
	});
</script>

<div class="sender-chart">
	<button class="section-toggle" onclick={() => collapsed = !collapsed}>
		<span class="toggle-icon">{collapsed ? '▸' : '▾'}</span>
		<span class="toggle-title">People</span>
		<span class="toggle-count">{Object.keys(senders).length}</span>
	</button>
	{#if !collapsed}
		<div class="chart-area">
			<canvas bind:this={canvas}></canvas>
		</div>
	{/if}
</div>

<style>
	.sender-chart {
		background: var(--bg-card);
		border-radius: var(--radius);
		height: 100%;
		display: flex;
		flex-direction: column;
	}

	.section-toggle {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.75rem 1rem;
		background: none;
		border: none;
		cursor: pointer;
		color: var(--text-primary);
	}

	.section-toggle:hover { background: var(--bg-hover); }

	.toggle-icon {
		font-size: 0.7rem;
		color: var(--text-muted);
		width: 0.8rem;
	}

	.toggle-title {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--text-secondary);
		font-weight: 600;
	}

	.toggle-count {
		margin-left: auto;
		font-size: 0.72rem;
		color: var(--text-muted);
		font-family: var(--font-mono);
	}

	.chart-area {
		height: 300px;
		position: relative;
		padding: 0.5rem 1rem 1rem;
	}

	canvas {
		background: transparent !important;
		cursor: pointer;
	}
</style>
