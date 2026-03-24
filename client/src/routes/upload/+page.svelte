<script lang="ts">
    import { Button } from "$lib/components/ui/button";

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
    }

    // Function to execute when the selected file changes.
    function onFileChange() {
        error = "";
        result = null;
        saveResult = null;

        const file = files?.[0];
        if (previewURL) URL.revokeObjectURL(previewURL);
        previewURL = file ? URL.createObjectURL(file) : "";
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
                throw new Error(`Server error: ${res.status}`);
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

        try {
            const buffer = await file.arrayBuffer();
            const base64 = btoa(String.fromCharCode(...new Uint8Array(buffer)));

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

            // TODO: Replace alert with something nicer later
            alert("Successfully saved document!");
        } catch (err) {
            error =
                err instanceof Error ? err.message : "Something went wrong.";
        } finally {
            saving = false;
        }
    }
</script>

<h2 class="text-3xl text-center">Upload a file</h2>

<div class="flex flex-col gap-2 items-center justify-center p-10">
    <input
        accept="image/png, image/jpeg, image/tiff, application/pdf"
        bind:files
        type="file"
        onchange={onFileChange}
    />
    <p class="text-sm text-muted-foreground">
        Supported: PNG, JPEG, TIFF, PDF (single-page)
    </p>
    {#if previewURL != ""}
        <img src={previewURL} alt="Preview" class="max-w-xs max-h-64 rounded" />
    {/if}
    <button onclick={clear}>Clear</button>
    <button onclick={ocr}>Run OCR</button>
</div>

<div class="flex flex-col gap-2 items-center justify-center p-10">
    {#if result}
        <p class="font-semibold {confidenceColor(result.avg_conf)}">
            Confidence: {result.avg_conf}
        </p>
        <p>{result.text}</p>

        {#if saving}
            <p>Saving to database...</p>
        {:else}
            <button onclick={save}>Save Document</button>
        {/if}

        {#if saveResult}
            <p class="font-semibold">Category: {saveResult.category}</p>
            <p class="font-semibold">Keywords:</p>
            <ul>
                {#each saveResult.keywords as word, conf}
                    <li>{word}, {conf}</li>
                {/each}
            </ul>
        {/if}
    {:else if loading}
        <p>Loading result...</p>
    {/if}

    {#if error != ""}
        <p class="text-red-100">{error}</p>
    {/if}
</div>

<div class="p-8">
    <Button onclick={() => (window.location.href = "/")}>Go home</Button>
</div>
