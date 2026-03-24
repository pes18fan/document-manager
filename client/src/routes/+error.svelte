<script lang="ts">
    import { page } from "$app/state";
</script>

<div class="p-8 m-8 flex flex-col gap-1 justify-center items-center min-w-0">
    <h1 class="text-5xl text-center p-10 font-bold">{page.status}</h1>
    <p class="text-muted-foreground text-m">{page.error!.message}</p>
</div>
