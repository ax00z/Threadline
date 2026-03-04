<script lang="ts">
	import { onMount } from 'svelte';
	import type { Message } from '$lib/types';
	import {
		Chart,
		BarController,
		CategoryScale,
		LinearScale,
		BarElement,
		Tooltip
	} from 'chart.js';

	Chart.register(BarController, CategoryScale, LinearScale, BarElement, Tooltip);

	let { messages }: { messages: Message[] } = $props();

	let canvas: HTMLCanvasElement;
	let chart: Chart | undefined;

	function buildDailyCounts() {
		const counts = new Map<string, number>();
		for (const m of messages) {
			const day = m.timestamp.slice(0, 10);
			counts.set(day, (counts.get(day) || 0) + 1);
		}
		const sorted = [...counts.keys()].sort();
		if (sorted.length < 2)
			return { labels: sorted, values: sorted.map((d) => counts.get(d) || 0) };
		const start = new Date(sorted[0]);
		const end = new Date(sorted[sorted.length - 1]);
		const labels: string[] = [];
		const values: number[] = [];
		for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
			const key = d.toISOString().slice(0, 10);
			labels.push(key);
			values.push(counts.get(key) || 0);
		}
		return { labels, values };
	}

	onMount(() => {
		const dc = buildDailyCounts();
		if (dc.labels.length === 0) return;

		requestAnimationFrame(() => {
			chart = new Chart(canvas, {
				type: 'bar',
				data: {
					labels: dc.labels,
					datasets: [
						{
							data: dc.values,
							backgroundColor: '#4f8ff740',
							borderColor: '#4f8ff7',
							borderWidth: 1,
							borderRadius: 2
						}
					]
				},
				options: {
					responsive: true,
					maintainAspectRatio: false,
					plugins: {
						legend: { display: false },
						tooltip: {
							callbacks: {
								title: (items: any[]) => {
									const d = new Date(items[0].label);
									return d.toLocaleDateString('en-US', {
										weekday: 'short',
										month: 'short',
										day: 'numeric',
										year: 'numeric'
									});
								},
								label: (ctx: any) => `${ctx.raw.toLocaleString()} messages`
							}
						}
					},
					scales: {
						x: {
							grid: { color: '#2e3140' },
							ticks: {
								color: '#8b8fa3',
								maxRotation: 0,
								maxTicksLimit: 12,
								callback: function (_: any, index: number) {
									const label = dc.labels[index];
									if (!label) return '';
									const d = new Date(label);
									return d.toLocaleDateString('en-US', {
										month: 'short',
										day: 'numeric'
									});
								}
							}
						},
						y: {
							beginAtZero: true,
							grid: { color: '#2e3140' },
							ticks: { color: '#8b8fa3' }
						}
					}
				}
			});
		});

		return () => chart?.destroy();
	});
</script>

<div class="timeline">
	<h3>Activity Timeline</h3>
	<div class="chart-area">
		<canvas bind:this={canvas}></canvas>
	</div>
</div>

<style>
	.timeline {
		background: var(--bg-card);
		border-radius: var(--radius);
		padding: 1rem;
	}

	h3 {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--text-secondary);
		margin-bottom: 0.75rem;
	}

	.chart-area {
		height: 200px;
		position: relative;
	}
</style>
