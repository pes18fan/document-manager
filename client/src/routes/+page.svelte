<script lang="ts">
    import * as Card from "$lib/components/ui/card";
    import * as AlertDialog from "$lib/components/ui/alert-dialog";
    import * as Dialog from "$lib/components/ui/dialog";
    import * as Empty from "$lib/components/ui/empty";
    import { Textarea } from "$lib/components/ui/textarea";
    import { Badge } from "$lib/components/ui/badge";
    import type { PageProps } from "./$types";
    import { Button } from "$lib/components/ui/button";
    import { invalidateAll } from "$app/navigation";

    interface Keyword {
        id: number;
        document_id: number;
        keyword: string;
        tfidf_score: number;
    }

    let { data }: PageProps = $props();

    const API_URL = "http://127.0.0.1:8000";

    let deleteDialogOpen = $state(false);
    let docToDelete: number | null = $state(null);
    let isDeleting = $state(false);

    // Document detail dialog state
    let detailDialogOpen = $state(false);
    let selectedDocId: number | null = $state(null);
    let selectedDocDetails: any = $state(null);
    let loadingDetails = $state(false);

    // Text editing state
    let isEditingText = $state(false);
    let editedText = $state("");
    let isSavingText = $state(false);

    // Keyword loading status
    let keywords: Keyword[] | null = $state(null);
    let loadingKeywords = $state(false);

    // Get the selected document from the data
    let selectedDoc = $derived(
        selectedDocId
            ? data.documents.find((d) => d.id === selectedDocId)
            : null,
    );

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

    async function getDocumentKeywords(id: number) {
        loadingKeywords = true;

        try {
            const res = await fetch(`${API_URL}/documents/${id}/keywords`);

            if (!res.ok) {
                throw new Error(`Server error: ${res.status}`);
            }

            keywords = await res.json();
        } catch (err) {
            console.error("Failed to fetch keywords:", err);
            alert(
                err instanceof Error ? err.message : "Failed to load keywords",
            );
        } finally {
            loadingKeywords = false;
        }
    }

    // Open document detail dialog
    async function openDocumentDetail(id: number) {
        selectedDocId = id;
        detailDialogOpen = true;
        loadingDetails = true;

        try {
            // Fetch full document details including keywords
            const res = await fetch(`${API_URL}/documents/${id}`);

            if (!res.ok) {
                throw new Error(`Server error: ${res.status}`);
            }

            selectedDocDetails = await res.json();
        } catch (err) {
            console.error("Failed to fetch document details:", err);
            alert(
                err instanceof Error
                    ? err.message
                    : "Failed to load document details",
            );
        } finally {
            loadingDetails = false;
        }

        try {
            await getDocumentKeywords(id);
        } catch (err) {
            console.error(err);
        }
    }

    function closeDocumentDetail() {
        detailDialogOpen = false;
        selectedDocId = null;
        selectedDocDetails = null;
        keywords = null;
        isEditingText = false;
        editedText = "";
    }

    function startEditingText() {
        if (selectedDoc) {
            editedText = selectedDoc.raw_text;
            isEditingText = true;
        }
    }

    function cancelEditingText() {
        isEditingText = false;
        editedText = "";
    }

    async function saveEditedText() {
        if (!selectedDocId || !editedText.trim()) {
            return;
        }

        isSavingText = true;

        try {
            const res = await fetch(
                `${API_URL}/documents/${selectedDocId}/text`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        raw_text: editedText,
                    }),
                },
            );

            if (!res.ok) {
                throw new Error(`Server error: ${res.status}`);
            }

            const result = await res.json();

            // Update the local document data
            if (selectedDoc) {
                selectedDoc.raw_text = editedText;
                selectedDoc.category = result.category;
                selectedDoc.cluster_id = result.cluster_id;
            }

            // Update the details with new keywords
            selectedDocDetails.keywords = result.keywords.map(
                ([keyword, score]: [string, number]) => ({
                    keyword,
                    tfidf_score: score,
                }),
            );

            // Refresh the page data to reflect changes in the card view
            await invalidateAll();

            isEditingText = false;
            editedText = "";
        } catch (err) {
            alert(
                err instanceof Error
                    ? err.message
                    : "Failed to update document text",
            );
            console.error(err);
        } finally {
            isSavingText = false;
        }
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
        <Empty.Root class="border border-dashed">
            <Empty.Header>
                <Empty.Media variant="icon">
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
                </Empty.Media>
                <Empty.Title>No Documents</Empty.Title>
                <Empty.Description>
                    Get started by uploading your first document.
                </Empty.Description>
            </Empty.Header>
            <Empty.Content>
                <Button
                    onclick={() => (window.location.href = "/upload")}
                    size="sm">Upload your first document</Button
                >
            </Empty.Content>
        </Empty.Root>
    {:else}
        <div
            class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
        >
            {#each data.documents as doc}
                <Card.Root
                    class="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
                    onclick={() => openDocumentDetail(doc.id)}
                >
                    <Card.Content class="p-0">
                        <div
                            class="aspect-3/4 bg-muted flex items-center justify-center overflow-hidden"
                        >
                            <img
                                src={`${API_URL}/documents/${doc.id}/preview`}
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
                                onclick={(e) => {
                                    e.stopPropagation();
                                    confirmDelete(doc.id);
                                }}
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

<!-- Document Detail Dialog -->
<Dialog.Root
    open={detailDialogOpen}
    onOpenChange={(open) => {
        if (!open) closeDocumentDetail();
    }}
>
    <Dialog.Content
        class="max-w-[80vw]! sm:max-w-[80vw]! max-h-[95vh] overflow-hidden flex flex-col"
    >
        <Dialog.Header>
            <Dialog.Title>Document Details</Dialog.Title>
            <Dialog.Description>
                View all information about this document
            </Dialog.Description>
        </Dialog.Header>

        {#if loadingDetails}
            <div class="flex items-center justify-center py-20">
                <div class="text-center">
                    <div
                        class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"
                    ></div>
                    <p class="text-muted-foreground">
                        Loading document details...
                    </p>
                </div>
            </div>
        {:else if selectedDoc && selectedDocDetails}
            <!-- Scrollable content area -->
            <div class="overflow-y-auto flex-1 pr-2">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 py-4">
                    <!-- Left Column -->
                    <div class="space-y-6">
                        <!-- Document Image -->
                        <div>
                            <h3 class="text-sm font-semibold mb-3">
                                Preview Image
                            </h3>
                            <div
                                class="border border-border rounded-lg overflow-hidden bg-muted"
                            >
                                <img
                                    src={`${API_URL}/documents/${selectedDoc.id}/preview`}
                                    alt={selectedDoc.filename}
                                    class="w-full h-auto max-h-96 object-contain"
                                />
                            </div>
                        </div>

                        <!-- Basic Information -->
                        <div class="space-y-4">
                            <h3 class="text-sm font-semibold">
                                Basic Information
                            </h3>

                            <div class="grid gap-3">
                                <div>
                                    <p
                                        class="text-xs text-muted-foreground mb-1"
                                    >
                                        Document ID
                                    </p>
                                    <p class="text-sm font-mono">
                                        {selectedDoc.id}
                                    </p>
                                </div>

                                <div>
                                    <p
                                        class="text-xs text-muted-foreground mb-1"
                                    >
                                        Filename
                                    </p>
                                    <p class="text-sm break-all">
                                        {selectedDoc.filename}
                                    </p>
                                </div>

                                <div>
                                    <p
                                        class="text-xs text-muted-foreground mb-1"
                                    >
                                        Uploaded At
                                    </p>
                                    <p class="text-sm">
                                        {new Date(
                                            selectedDoc.uploaded_at,
                                        ).toLocaleString()}
                                    </p>
                                </div>

                                <div>
                                    <p
                                        class="text-xs text-muted-foreground mb-1"
                                    >
                                        Category
                                    </p>
                                    <div>
                                        <Badge
                                            variant={getCategoryVariant(
                                                selectedDoc.category,
                                            )}
                                        >
                                            {selectedDoc.category}
                                        </Badge>
                                    </div>
                                </div>

                                <div>
                                    <p
                                        class="text-xs text-muted-foreground mb-1"
                                    >
                                        OCR Confidence
                                    </p>
                                    <p
                                        class="text-sm font-semibold {selectedDoc.avg_conf >=
                                        80
                                            ? 'text-green-600'
                                            : selectedDoc.avg_conf >= 50
                                              ? 'text-yellow-600'
                                              : 'text-red-600'}"
                                    >
                                        {selectedDoc.avg_conf.toFixed(2)}%
                                    </p>
                                </div>
                            </div>
                        </div>

                        <!-- Technical Details -->
                        <div class="space-y-4">
                            <h3 class="text-sm font-semibold">
                                Technical Details
                            </h3>

                            <div class="grid gap-3">
                                <div>
                                    <p
                                        class="text-xs text-muted-foreground mb-1"
                                    >
                                        Content Hash (SHA256)
                                    </p>
                                    <p
                                        class="text-xs font-mono break-all bg-muted p-2 rounded"
                                    >
                                        {selectedDoc.content_hash}
                                    </p>
                                </div>

                                <div>
                                    <p
                                        class="text-xs text-muted-foreground mb-1"
                                    >
                                        Cluster ID
                                    </p>
                                    <p class="text-sm">
                                        {selectedDoc.cluster_id ?? "N/A"}
                                    </p>
                                </div>

                                <div>
                                    <p
                                        class="text-xs text-muted-foreground mb-1"
                                    >
                                        Image Path
                                    </p>
                                    <p
                                        class="text-xs font-mono break-all bg-muted p-2 rounded"
                                    >
                                        {selectedDoc.image_path}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Right Column -->
                    <div class="space-y-6">
                        <!-- Full Text Content -->
                        <div class="space-y-4 flex-1">
                            <div class="flex items-center justify-between">
                                <h3 class="text-sm font-semibold">
                                    Extracted Text
                                </h3>
                                {#if !isEditingText}
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onclick={startEditingText}
                                    >
                                        Edit Text
                                    </Button>
                                {/if}
                            </div>

                            {#if isEditingText}
                                <div class="space-y-3">
                                    <Textarea
                                        bind:value={editedText}
                                        class="font-mono text-sm resize-none"
                                        rows={25}
                                        placeholder="Edit the extracted text..."
                                    />
                                    <div class="flex gap-2">
                                        <Button
                                            onclick={saveEditedText}
                                            disabled={isSavingText ||
                                                !editedText.trim()}
                                            size="sm"
                                        >
                                            {isSavingText
                                                ? "Saving..."
                                                : "Save Changes"}
                                        </Button>
                                        <Button
                                            variant="outline"
                                            onclick={cancelEditingText}
                                            disabled={isSavingText}
                                            size="sm"
                                        >
                                            Cancel
                                        </Button>
                                    </div>
                                    <p class="text-xs text-muted-foreground">
                                        Note: Saving will re-run NLP analysis
                                        and update keywords & category.
                                    </p>
                                </div>
                            {:else}
                                <div
                                    class="bg-muted p-4 rounded-lg border border-border max-h-[500px] overflow-y-auto"
                                >
                                    <p class="text-sm whitespace-pre-wrap">
                                        {selectedDoc.raw_text}
                                    </p>
                                </div>
                            {/if}
                        </div>

                        <!-- Keywords -->
                        {#if keywords && keywords.length > 0}
                            <div class="space-y-4">
                                <h3 class="text-sm font-semibold">
                                    Keywords (TF-IDF)
                                </h3>
                                <div class="flex flex-wrap gap-2">
                                    {#each keywords as keyword}
                                        <span
                                            class="bg-secondary text-secondary-foreground px-3 py-1.5 rounded-full text-xs"
                                        >
                                            {keyword.keyword}
                                            <span
                                                class="text-muted-foreground ml-1"
                                            >
                                                ({keyword.tfidf_score.toFixed(
                                                    4,
                                                )})
                                            </span>
                                        </span>
                                    {/each}
                                </div>
                            </div>
                        {/if}
                    </div>
                </div>
            </div>

            <Dialog.Footer class="flex gap-2 mt-4">
                <Button variant="outline" onclick={closeDocumentDetail}>
                    Close
                </Button>
                <Button
                    variant="destructive"
                    onclick={async () => {
                        closeDocumentDetail();
                        if (selectedDoc) {
                            await confirmDelete(selectedDoc.id);
                        }
                    }}
                >
                    Delete Document
                </Button>
            </Dialog.Footer>
        {/if}
    </Dialog.Content>
</Dialog.Root>

<!-- Delete Confirmation Dialog -->
<AlertDialog.Root open={deleteDialogOpen}>
    <AlertDialog.Content>
        <AlertDialog.Header>
            <AlertDialog.Title>Delete Document</AlertDialog.Title>
            <AlertDialog.Description>
                Are you sure you want to delete this document? This action
                cannot be undone.
            </AlertDialog.Description>
        </AlertDialog.Header>
        <AlertDialog.Footer>
            <AlertDialog.Cancel onclick={cancelDelete} disabled={isDeleting}>
                Cancel
            </AlertDialog.Cancel>
            <AlertDialog.Action onclick={performDelete} disabled={isDeleting}>
                {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialog.Action>
        </AlertDialog.Footer>
    </AlertDialog.Content>
</AlertDialog.Root>
