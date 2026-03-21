<script lang="ts">
    import "./layout.css";
    import favicon from "$lib/assets/favicon.svg";

    let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
<main>
    <h1 class="text-5xl text-center p-10 font-bold">Doc Manager</h1>
    {@render children()}
</main>
