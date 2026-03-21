<script lang="ts">
    const docs = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "Etiam condimentum neque et porttitor malesuada.",
        "Aliquam lacinia tortor sit amet molestie consequat.",
        "In at lectus id mi commodo porta a a quam.",
        "In eget neque at orci finibus semper non nec nunc.",
    ];
</script>

<div class="grid grid-cols-4 gap-4 p-6">
    {#each docs as i}
        <div class="p-4 text-center outline-2 outline-solid">{i}</div>
    {/each}
</div>
