<script lang="ts">
    import { Badge } from "$lib/components/ui/badge";
    import * as Card from "$lib/components/ui/card";
    import type { PageProps } from "./$types";
    import { Button } from "$lib/components/ui/button/index.js";
    import { invalidateAll } from "$app/navigation";
    import {
        AlertDialog,
        AlertDialogContent,
        AlertDialogHeader,
        AlertDialogTitle,
        AlertDialogDescription,
        AlertDialogFooter,
        AlertDialogAction,
        AlertDialogCancel,
    } from "$lib/components/ui/alert-dialog";

    let { data }: PageProps = $props();

    const API_URL = "http://127.0.0.1:8000";

    let deleteDialogOpen = $state(false);
    let docToDelete: number | null = $state(null);
    let isDeleting = $state(false);

    async function confirmDelete(id: number) {
        docToDelete = id;
        deleteDialogOpen = true;
    }

    async function performDelete() {
        if (docToDelete === null) return;

        isDeleting = true;

        try {
            const res = await fetch(`${API_URL}/documents/${docToDelete}`, {
                method: "DELETE",
            });

            if (!res.ok) {
                throw new Error(`Server error: ${res.status}`);
            }

            deleteDialogOpen = false;
            docToDelete = null;

            // Refresh the page data to reflect the deletion
            await invalidateAll();
        } catch (err) {
            alert(err instanceof Error ? err.message : "Failed to delete document");
            console.error(err);
            isDeleting = false;
        }
    }

    function cancelDelete() {
        deleteDialogOpen = false;
        docToDelete = null;
    }

    // Truncate a filename from the middle.
    // "abcdefghijklmno.jpg" -> "abc...mno.jpg"
    function truncateMiddle(filename: string, maxLength = 20) {
        const ext = filename.slice(filename.lastIndexOf("."));
        const name = filename.slice(0, filename.lastIndexOf("."));
        if (name.length <= maxLength) return filename;
        const keep = Math.floor((maxLength - 3) / 2);
        return name.slice(0, keep) + "..." + name.slice(-keep) + ext;
    }

    // Map categories to badge variants or custom colors
    function getCategoryVariant(
        category: string,
    ): "default" | "secondary" | "destructive" | "outline" | "ghost" | "link" {
        const categoryMap: Record<
            string,
            | "default"
            | "secondary"
            | "destructive"
            | "outline"
            | "ghost"
            | "link"
        > = {
            Politics: "default",
            Finance: "secondary",
            Sports: "destructive",
            Society: "outline",
            Health: "ghost",
        };
        return categoryMap[category] || "default";
    }
</script>

<div class="grid grid-cols-4">
    {#each data.documents as doc}
        <Card.Root
            class="p-8 m-8 flex flex-col justify-center items-center min-w-0"
        >
            <Card.Content class="flex justify-center items-center">
                <img
                    src={`${API_URL}/${doc.image_path}`}
                    alt="Preview"
                    class="max-w-xs max-h-64 rounded"
                />
            </Card.Content>
            <Card.Footer class="flex flex-col items-start gap-2">
                <p>{truncateMiddle(doc.filename)}</p>
                <p class="text-muted-foreground text-sm">
                    {doc.raw_text.slice(0, 50)}...
                </p>
                <Badge variant={getCategoryVariant(doc.category)}
                    >{doc.category}</Badge>
            </Card.Footer>
            <Card.Footer class="mt-auto">
                <Button 
                    variant="destructive" size="sm" 
                    onclick={() => confirmDelete(doc.id)}>
                    Delete
                </Button>
            </Card.Footer>
        </Card.Root>
    {/each}
</div>

<AlertDialog open={deleteDialogOpen}>
    <AlertDialogContent>
        <AlertDialogHeader>
            <AlertDialogTitle>Delete Document</AlertDialogTitle>
            <AlertDialogDescription>
                Are you sure you want to delete this document? This action cannot be undone.
            </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
            <AlertDialogCancel onclick={cancelDelete} disabled={isDeleting}>
                Cancel
            </AlertDialogCancel>
            <AlertDialogAction onclick={performDelete} disabled={isDeleting}>
                {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
        </AlertDialogFooter>
    </AlertDialogContent>
</AlertDialog>

<div class="p-8">
    <Button onclick={() => (window.location.href = "/upload")}
        >Add a new file</Button
    >
</div>
