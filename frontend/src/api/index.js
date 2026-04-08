const API_BASE_URL = 'http://localhost:8000/api';

function getAuthHeaders() {
  const token = localStorage.getItem('codex_token');
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Ingest a repository into the CodEx backend
 */
export async function ingestRepo(repoUrl) {
  const response = await fetch(`${API_BASE_URL}/ingest`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ repo_url: repoUrl }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to ingest repository');
  }

  return response.json();
}

/**
 * Check ingestion status
 */
export async function getIngestionStatus(repoName) {
  const response = await fetch(`${API_BASE_URL}/ingest/status/${encodeURIComponent(repoName)}`, {
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    throw new Error('Failed to get ingestion status');
  }
  
  return response.json();
}

/**
 * Get all ingested repositories
 */
export async function getRepos() {
  const response = await fetch(`${API_BASE_URL}/repos`, {
    headers: getAuthHeaders(),
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch repositories');
  }
  
  return response.json();
}

/**
 * Set up SSE for streaming RAG queries
 */
export function createQueryStream(question, repoName, onChunk, onDone, onError) {
  return new Promise((resolve, reject) => {
    fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        question,
        repo_name: repoName,
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Failed to execute query');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        async function processStream() {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n\n');
              buffer = lines.pop() || '';

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6));
                    if (data.type === 'chunk') {
                      onChunk(data.content);
                    } else if (data.type === 'done') {
                      onDone(data);
                    } else if (data.type === 'error') {
                      onError(new Error(data.content));
                    }
                  } catch (e) {
                    console.error('Failed to parse SSE data:', line, e);
                  }
                }
              }
            }
            // Stream manually closed
            resolve();
          } catch (err) {
            onError(err);
            reject(err);
          }
        }

        processStream();
      })
      .catch((err) => {
        onError(err);
        reject(err);
      });
  });
}
