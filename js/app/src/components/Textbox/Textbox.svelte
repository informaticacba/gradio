<svelte:options accessors={true} />

<script lang="ts">
	import { TextBox } from "@gradio/form";
	import { Block } from "@gradio/atoms";
	import StatusTracker from "../StatusTracker/StatusTracker.svelte";
	import type { LoadingStatus } from "../StatusTracker/types";

	export let label: string = "Textbox";
	export let info: string | undefined = undefined;
	export let elem_id: string = "";
	export let elem_classes: Array<string> = [];
	export let visible: boolean = true;
	export let value: string = "";
	export let lines: number;
	export let placeholder: string = "";
	export let show_label: boolean;
	export let max_lines: number;
	export let type: "text" | "password" | "email" = "text";
	export let container: boolean = false;
	export let scale: number | null = null;
	export let min_width: number | undefined = undefined;
	export let show_copy_button: boolean = false;
	export let loading_status: LoadingStatus | undefined = undefined;
	export let mode: "static" | "dynamic";
	export let value_is_output: boolean = false;
</script>

<Block {visible} {elem_id} {elem_classes} {scale} {min_width} {container}>
	{#if loading_status}
		<StatusTracker {...loading_status} />
	{/if}

	<TextBox
		bind:value
		bind:value_is_output
		{label}
		{info}
		{show_label}
		{lines}
		{type}
		max_lines={!max_lines && mode === "static" ? lines + 1 : max_lines}
		{placeholder}
		{show_copy_button}
		on:change
		on:input
		on:submit
		on:blur
		on:select
		disabled={mode === "static"}
	/>
</Block>
