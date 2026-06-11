// frontend/src/api.ts
const API_BASE_URL = "http://localhost:8000";

export const analyzeRepository = async (repoPath: string) => {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ repo_path: repoPath }), 
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to analyze repository");
    }

    return response.json();
};