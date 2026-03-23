<script lang="ts">
    // TODO: Replace this with an array of documents or something
    const arr = [0, 1, 2, 3, 4, 5, 6, 7, 8];
</script>

<div class="grid grid-cols-4">
    {#each arr as i}
        <div
            class="p-4 m-4 outline-2 outline-solid flex justify-center align-center"
        >
            {i}
        </div>
    {/each}
</div>

<a href="/upload">Add a new file</a>
