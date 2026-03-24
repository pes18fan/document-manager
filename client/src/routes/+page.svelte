<script lang="ts">
    import { Badge } from "$lib/components/ui/badge";
    import * as Card from "$lib/components/ui/card";
    import type { PageProps } from "./$types";
    import { Button } from "$lib/components/ui/button/index.js";

    let { data }: PageProps = $props();

    const API_URL = "http://127.0.0.1:8000";

    // Truncate a filename from the middle.
    // "abcdefghijklmno.jpg" -> "abc...mno.jpg"
    function truncateMiddle(filename: string, maxLength = 20) {
        const ext = filename.slice(filename.lastIndexOf("."));
        const name = filename.slice(0, filename.lastIndexOf("."));
        if (name.length <= maxLength) return filename;
        const keep = Math.floor((maxLength - 3) / 2);
        return name.slice(0, keep) + "..." + name.slice(-keep) + ext;
    }
</script>

<div class="grid grid-cols-4">
    {#each data.documents as doc}
        <Card.Root
            class="p-8 m-8 flex flex-col justify-center align-center min-w-0"
        >
            <Card.Content class="flex justify-center align-center">
                <img
                    src={`${API_URL}/${doc.image_path}`}
                    alt="Preview"
                    class="max-w-xs max-h-64 rounded"
                />
            </Card.Content>
            <Card.Footer class="flex flex-col items-start">
                <p>{truncateMiddle(doc.filename)}</p>
                <p class="text-muted-foreground text-sm">
                    {doc.raw_text.slice(0, 50)}...
                </p>
                <Badge>{doc.category}</Badge>
            </Card.Footer>
        </Card.Root>

        <!-- <div -->
        <!--     class="p-8 m-8 outline-2 outline-solid flex flex-col justify-center align-center min-w-0" -->
        <!-- ></div> -->
    {/each}
</div>

<div class="p-8">
    <Button onclick={() => window.location.href = "/upload"}>Add a new file</Button>
</div>
