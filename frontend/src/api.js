// API client for the ADR-9000 documentation generator backend.
// Adjust VITE_API_BASE_URL in your .env if the backend isn't on localhost:8000.

const API_BASE = import.meta.env.VITE_API_BASE_URL ;

async function handleResponse(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // response wasn't JSON, fall back to statusText
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

// POST /api/runs/create — kicks off a documentation run for a repo.
// Returns something like { run_id, status } per CreateRunRequest/RunResponse.
export async function createRun(repoUrl) {
  const trimmed = (repoUrl || '').trim();
  if (!trimmed) {
    throw new Error('Enter a repository URL before generating docs.');
  }

  const res = await fetch(`${API_BASE}/api/runs/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url: trimmed }),
  });
  return handleResponse(res);
}

// GET /api/jobs/{run_id} — polls run status.
export async function getRunStatus(runId) {
  const res = await fetch(`${API_BASE}/api/jobs/${runId}`);
  return handleResponse(res);
}

// GET /api/runs/{run_id}/artifacts — fetches generated ADRs once the run is done.
export async function getRunArtifacts(runId) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/artifacts`);
  return handleResponse(res);
}

