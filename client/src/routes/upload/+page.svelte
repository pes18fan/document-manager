<script lang="ts">
    import { Button } from "$lib/components/ui/button";
    import { Input } from "$lib/components/ui/input/index.js";
    import { Label } from "$lib/components/ui/label/index.js";
    import {
        AlertDialog,
        AlertDialogContent,
        AlertDialogHeader,
        AlertDialogTitle,
        AlertDialogDescription,
        AlertDialogFooter,
        AlertDialogAction,
    } from "$lib/components/ui/alert-dialog";

    // What the result of an "/ocr" POST request looks like.
    interface OcrResult {
        filename: string;
        text: string;
        avg_conf: number;
        words: { text: string; conf: number; bbox: number[] }[];
    }

    type Keyword = [string, number];

    // What the result of a "/document" POST request looks like.
    interface SaveResult {
        id: number;
        category: string;
        keywords: Keyword[];
    }

    // URL to the server
    const API_URL = "http://127.0.0.1:8000";

    // File selected for OCR. It is a FileList as the bind:files input type in
    // Svelte only works with lists; however this list must never have more
    // than one selected file.
    let files: FileList = $state(new DataTransfer().files); // file selected for OCR

    // The current OCR result.
    let result: OcrResult | null = $state(null);

    // The current result obtained after saving a doc to the database.
    let saveResult: SaveResult | null = $state(null);

    // URL to a preview of the selected document.
    let previewURL = $state("");

    // Whether the OCR result is loading or not.
    let loading = $state(false);

    // Whether a database save request is currently processing or not.
    let saving = $state(false);

    // An error that occured during any of the processes. Empty if no error.
    let error = $state("");

    // If document has been successfully uploaded.
    let uploadSuccess = $state(false);

    // Return a Tailwind class describing a color associated with the provided
    // confidence level.
    function confidenceColor(conf: number): string {
        if (conf >= 80) return "text-green-600";
        if (conf >= 50) return "text-yellow-600";
        return "text-red-600";
    }

    // Remove the selected file and clear all results and errors.
    function clear() {
        files = new DataTransfer().files; // null or undefined does not work
        error = "";
        result = null;
        saveResult = null;
        previewURL = "";
        uploadSuccess = false;
    }

    // Function to execute when the selected file changes.
    function onFileChange() {
        error = "";
        result = null;
        saveResult = null;

        const file = files?.[0];
        if (previewURL) URL.revokeObjectURL(previewURL);

        if (!file) {
            previewURL = "";
            return;
        }

        // For PDFs, we don't preview them - conversion happens on backend
        if (file.type === "application/pdf") {
            previewURL = "";
        } else {
            previewURL = URL.createObjectURL(file);
        }
    }

    // Function called to run OCR through a request to the server.
    async function ocr() {
        const file = files.item(0);

        if (!file) {
            error = "No file selected.";
            return;
        }

        loading = true;
        error = "";

        try {
            const form = new FormData();
            form.append("file", file);

            const res = await fetch(`${API_URL}/ocr`, {
                method: "POST",
                body: form,
            });

            if (!res.ok) {
                let errorMessage = `Server error: ${res.status}`;
                try {
                    const errorData = await res.json();
                    if (errorData.detail) {
                        errorMessage = errorData.detail;
                    }
                } catch {
                    // If response is not JSON, use status code message
                }
                throw new Error(errorMessage);
            }

            const data: OcrResult = await res.json();
            result = data;
        } catch (err) {
            error =
                err instanceof Error ? err.message : "Something went wrong.";
        } finally {
            loading = false;
        }
    }

    // Function called to save a document to the database through a server
    // request.
    async function save() {
        if (!result) {
            error = "No processed document selected.";
            return;
        }

        if (!files) {
            error = "No file selected.";
            return;
        }

        const file = files.item(0);
        if (!file) {
            error = "No file selected.";
            return;
        }

        saving = true;
        error = "";
        uploadSuccess = false;

        try {
            const buffer = await file.arrayBuffer();
            const bytes = new Uint8Array(buffer);
            let binary = '';
            for (let i = 0; i < bytes.byteLength; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            const base64 = btoa(binary);

            const body = JSON.stringify({
                filename: result.filename,
                raw_text: result.text,
                avg_conf: result.avg_conf,
                image_data: base64,
            });

            const res = await fetch(`${API_URL}/documents`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: body,
            });

            if (!res.ok) {
                throw new Error(`Server error: ${res.status}`);
            }

            const data: SaveResult = await res.json();
            saveResult = data;

            uploadSuccess = true; // Set to true to trigger a redirect in the +page.svelte file.

        } catch (err) {
            error =
                err instanceof Error ? err.message : "Something went wrong.";
        } finally {
            saving = false;
        }
    }
</script>

<div class="container mx-auto p-6 max-w-7xl">
    <h2 class="text-3xl font-bold mb-8">Upload Document</h2>

    <!-- Two-paned layout -->
    <div class="grid {result || loading ? 'grid-cols-2' : 'grid-cols-1'} gap-6 min-h-[600px]">
        <!-- Left Pane: Upload Controls -->
        <div class="flex flex-col {result || loading ? '' : 'items-center justify-center max-w-xl mx-auto w-full'}">
            <div class="border border-border rounded-lg p-8 bg-card">
                <h3 class="text-xl font-semibold mb-4">Select Document</h3>
                
                <div class="space-y-4">
                    <div>
                        <Label for="file-upload" class="mb-2">Choose a file</Label>
                        <Input
                            id="file-upload"
                            accept="image/png, image/jpeg, image/tiff, application/pdf"
                            bind:files
                            type="file"
                            onchange={onFileChange}
                            class="cursor-pointer"
                        />
                        <p class="text-sm text-muted-foreground mt-2">
                            Supported: PNG, JPEG, TIFF, PDF (single-page)
                        </p>
                    </div>

                    {#if previewURL != ""}
                        <div class="mt-4">
                            <Label class="mb-2">Preview</Label>
                            <img 
                                src={previewURL} 
                                alt="Preview" 
                                class="w-full max-h-64 object-contain rounded border border-border" 
                            />
                        </div>
                    {/if}

                    <div class="flex gap-2 pt-4">
                        <Button onclick={ocr} disabled={loading || !files[0]} class="flex-1">
                            {loading ? "Processing..." : "Run OCR"}
                        </Button>
                        <Button onclick={clear} variant="outline" disabled={loading}>
                            Clear
                        </Button>
                    </div>

                    {#if error != ""}
                        <div class="bg-destructive/10 border border-destructive/20 rounded p-3 text-sm text-destructive">
                            {error}
                        </div>
                    {/if}
                </div>
            </div>
        </div>

        <!-- Right Pane: Results (only visible when there are results) -->
        {#if result || loading}
            <div class="border border-border rounded-lg p-8 bg-card overflow-auto">
                <h3 class="text-xl font-semibold mb-4">Results</h3>
                
                {#if loading}
                    <div class="flex items-center justify-center h-64">
                        <div class="text-center">
                            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
                            <p class="text-muted-foreground">Processing document...</p>
                        </div>
                    </div>
                {:else if result}
                    <div class="space-y-6">
                        <!-- OCR Confidence -->
                        <div>
                            <Label class="mb-2">OCR Confidence</Label>
                            <p class="text-2xl font-bold {confidenceColor(result.avg_conf)}">
                                {result.avg_conf.toFixed(2)}%
                            </p>
                        </div>

                        <!-- Extracted Text -->
                        <div>
                            <Label class="mb-2">Extracted Text</Label>
                            <div class="bg-muted p-4 rounded border border-border whitespace-pre-wrap text-sm max-h-64 overflow-auto">
                                {result.text}
                            </div>
                        </div>

                        <!-- Save Button -->
                        {#if !saveResult}
                            <Button onclick={save} disabled={saving} class="w-full">
                                {saving ? "Saving to database..." : "Save Document"}
                            </Button>
                        {/if}

                        <!-- Save Results -->
                        {#if saveResult}
                            <div class="space-y-4 pt-4 border-t border-border">
                                <div>
                                    <Label class="mb-2">Category</Label>
                                    <p class="text-lg font-semibold">{saveResult.category}</p>
                                </div>
                                
                                <div>
                                    <Label class="mb-2">Keywords</Label>
                                    <div class="flex flex-wrap gap-2">
                                        {#each saveResult.keywords as [word, score]}
                                            <span class="bg-secondary text-secondary-foreground px-3 py-1 rounded-full text-sm">
                                                {word} <span class="text-muted-foreground">({score.toFixed(2)})</span>
                                            </span>
                                        {/each}
                                    </div>
                                </div>

                                <Button onclick={() => (window.location.href = "/")} variant="default" class="w-full">
                                    View All Documents
                                </Button>
                            </div>
                        {/if}
                    </div>
                {/if}
            </div>
        {/if}
    </div>
</div>

<!-- Success Dialog -->
{#if uploadSuccess}
    <AlertDialog open={uploadSuccess}>
        <AlertDialogContent>
            <AlertDialogHeader>
                <AlertDialogTitle>Success</AlertDialogTitle>
                <AlertDialogDescription>
                    Document successfully saved to the database!
                </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
                <AlertDialogAction onclick={() => (uploadSuccess = false)}>
                    OK
                </AlertDialogAction>
            </AlertDialogFooter>
        </AlertDialogContent>
    </AlertDialog>
{/if}
