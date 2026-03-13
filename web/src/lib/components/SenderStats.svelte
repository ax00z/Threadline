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

	onMount(() => {
		const sorted = Object.entries(senders).sort((a, b) => b[1] - a[1]);
		senderLabels = sorted.map(([name]) => name);
		const senderValues = sorted.map(([, count]) => count);
		const colorMap = buildSenderColorMap(senderLabels);
		baseColors = senderLabels.map((l) => colorMap.get(l) || '#555');

		if (senderLabels.length === 0) return;

		requestAnimationFrame(() => {
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
						x: { grid: { color: '#2e3140' }, ticks: { color: '#8b8fa3' } },
						y: { grid: { display: false }, ticks: { color: '#e1e4ea', font: { size: 11 } } }
					}
				}
			});
		});

		return () => chart?.destroy();
	});

	// dim bars that aren't the selected person
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
	<h3>People</h3>
	<div class="chart-area">
		<canvas bind:this={canvas}></canvas>
	</div>
</div>

<style>
	.sender-chart {
		background: var(--bg-card);
		border-radius: var(--radius);
		padding: 1rem;
		height: 100%;
		display: flex;
		flex-direction: column;
	}

	h3 {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--text-secondary);
		margin-bottom: 0.75rem;
	}

	.chart-area {
		height: 300px;
		position: relative;
	}

	canvas {
		background: transparent !important;
		cursor: pointer;
	}
</style>
