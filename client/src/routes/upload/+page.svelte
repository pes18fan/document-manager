<script lang="ts">
    interface OcrResult {
        text: string;
        avg_conf: number;
        words: { text: string; conf: number; bbox: number[] }[];
    }

    const API_URL = "http://127.0.0.1:8000";

    let files: FileList = $state(new DataTransfer().files);
    let result: OcrResult | null = $state(null);
    let previewUrl = $state("");
    let loading = $state(false);
    let error = $state("");

    function clear() {
        files = new DataTransfer().files; // null or undefined does not work
        error = "";
        result = null;
        previewUrl = "";
    }

    function onFileChange() {
        error = "";
        result = null;

        const file = files?.[0];
        if (previewUrl) URL.revokeObjectURL(previewUrl);
        previewUrl = file ? URL.createObjectURL(file) : "";
    }

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

    function confidenceColor(conf: number): string {
        if (conf >= 80) return "text-green-600";
        if (conf >= 50) return "text-yellow-600";
        return "text-red-600";
    }
</script>

<h2 class="text-3xl text-center">Upload a file</h2>

<div class="flex flex-col gap-2 items-center justify-center p-10">
    <input
        accept="image/png, image/jpeg, image/tiff"
        bind:files
        type="file"
        onchange={onFileChange}
    />
    {#if previewUrl != ""}
        <img src={previewUrl} alt="Preview" class="max-w-xs max-h-64 rounded" />
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
    {/if}

    {#if loading}
        <p>Loading result...</p>
    {/if}

    {#if error != ""}
        <p class="text-red-100">{error}</p>
    {/if}
</div>

<a href="/">Go home</a>
