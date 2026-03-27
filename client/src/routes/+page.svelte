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
            alert(
                err instanceof Error
                    ? err.message
                    : "Failed to delete document",
            );
            console.error(err);
        } finally {
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

<div class="container mx-auto p-6">
    <div class="flex justify-between items-center mb-8">
        <div>
            <h2 class="text-3xl font-bold">My Documents</h2>
            <p class="text-muted-foreground mt-1">
                {data.documents.length} document{data.documents.length !== 1
                    ? "s"
                    : ""} in your collection
            </p>
        </div>
    </div>

    {#if data.documents.length === 0}
        <div
            class="flex flex-col items-center justify-center py-20 text-center"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                class="text-muted-foreground mb-4"
                ><path
                    d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"
                /><polyline points="14 2 14 8 20 8" /></svg
            >
            <h3 class="text-xl font-semibold mb-2">No documents yet</h3>
            <p class="text-muted-foreground mb-6">
                Get started by uploading your first document
            </p>
            <Button onclick={() => (window.location.href = "/upload")}>
                Upload Your First Document
            </Button>
        </div>
    {:else}
        <div
            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
        >
            {#each data.documents as doc}
                <Card.Root
                    class="overflow-hidden hover:shadow-lg transition-shadow"
                >
                    <Card.Content class="p-0">
                        <div
                            class="aspect-[3/4] bg-muted flex items-center justify-center overflow-hidden"
                        >
                            <img
                                src={`${API_URL}/documents/preview/${doc.id}`}
                                alt={doc.filename}
                                class="w-full h-full object-cover"
                            />
                        </div>
                    </Card.Content>
                    <Card.Footer class="flex flex-col items-start gap-3 p-4">
                        <div class="w-full">
                            <p
                                class="font-semibold text-sm truncate"
                                title={doc.filename}
                            >
                                {truncateMiddle(doc.filename)}
                            </p>
                            <p
                                class="text-muted-foreground text-xs mt-1 line-clamp-2"
                            >
                                {doc.raw_text.slice(0, 80)}...
                            </p>
                        </div>
                        <div class="flex items-center justify-between w-full">
                            <Badge variant={getCategoryVariant(doc.category)}>
                                {doc.category}
                            </Badge>
                            <Button
                                variant="ghost"
                                size="icon"
                                class="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                                onclick={() => confirmDelete(doc.id)}
                                title="Delete document"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    width="16"
                                    height="16"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="2"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    ><path d="M3 6h18" /><path
                                        d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"
                                    /><path
                                        d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"
                                    /></svg
                                >
                            </Button>
                        </div>
                    </Card.Footer>
                </Card.Root>
            {/each}
        </div>
    {/if}
</div>

<!-- Delete Confirmation Dialog -->
<AlertDialog open={deleteDialogOpen}>
    <AlertDialogContent>
        <AlertDialogHeader>
            <AlertDialogTitle>Delete Document</AlertDialogTitle>
            <AlertDialogDescription>
                Are you sure you want to delete this document? This action
                cannot be undone.
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
