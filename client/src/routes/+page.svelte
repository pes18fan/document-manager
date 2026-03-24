<script lang="ts">
    import type { PageProps } from "./$types";

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
        <div
            class="p-8 m-8 outline-2 outline-solid flex flex-col justify-center align-center min-w-0"
        >
            <p>Filename: {truncateMiddle(doc.filename)}</p>
            <img
                src={`${API_URL}/${doc.image_path}`}
                alt="Preview"
                class="max-w-xs max-h-64 rounded"
            />
            <p>Text: {doc.raw_text.slice(0, 50)}...</p>
            <p>Category: {doc.category}</p>
        </div>
    {/each}
</div>

<a href="/upload">Add a new file</a>
