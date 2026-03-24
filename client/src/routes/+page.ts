import type { PageLoad } from './$types';

const API_URL = "http://127.0.0.1:8000";

interface Document {
    id: number;
    content_hash: string;
    filename: string;
    image_path: string;
    raw_text: string;
    avg_conf: number;
    uploaded_at: Date;
    cluster_id: number;
    category: string;
}

export const load: PageLoad = async () => {
    const res = await fetch(`${API_URL}/documents`);

    if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
    }

    const data: Document[] = await res.json();
    return {
        documents: data
    };
};
