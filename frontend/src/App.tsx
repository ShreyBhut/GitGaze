// frontend/src/App.tsx
import React, { useState } from 'react';
import { analyzeRepository } from './api';

function App() {
  const [repoPath, setRepoPath] = useState<string>('/app');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    
    try {
      const result = await analyzeRepository(repoPath);
      setData(result.data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1>GitGaze Dashboard</h1>
      
      <div style={{ marginBottom: '2rem' }}>
        <input 
          type="text" 
          value={repoPath} 
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRepoPath(e.target.value)}
          placeholder="Enter absolute repository path..."
          style={{ width: '300px', padding: '0.5rem', marginRight: '1rem' }}
        />
        <button 
          onClick={handleAnalyze} 
          disabled={loading}
          style={{ padding: '0.5rem 1rem', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? 'Analyzing...' : 'Analyze Repository'}
        </button>
      </div>

      {error && (
        <div style={{ color: 'red', marginBottom: '1rem', padding: '1rem', background: '#ffebee' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {data && (
        <div style={{ background: '#1e1e1e', color: '#a6e22e', padding: '1rem', borderRadius: '8px', overflowX: 'auto' }}>
          <h3>Raw Analysis Results:</h3>
          <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;