import { useState } from 'react';
// If you are importing an API layer or handling states differently, 
// keep your existing state declarations exactly as they are!

function App() {
  const [repoPath, setRepoPath] = useState('/app');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<any>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: repoPath }),
      });
      if (!response.ok) throw new Error('Analysis failed');
      const resData = await response.json();
      setData(resData);
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            GitGaze Dashboard
          </h1>
          <span className="text-xs bg-slate-800 text-slate-400 px-2.5 py-1 rounded-full border border-slate-700 font-mono">
            v1.0.0
          </span>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-6xl mx-auto p-6 space-y-6">
        
        {/* Input Controls Card */}
        <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row gap-4 items-end sm:items-center">
            <div className="flex-1 w-full">
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                Target Repository Path
              </label>
              <input 
                type="text" 
                value={repoPath} 
                onChange={(e) => setRepoPath(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-mono text-sm"
                placeholder="/path/to/repo"
              />
            </div>
            
            <button 
              onClick={handleAnalyze} 
              disabled={loading}
              className="w-full sm:w-auto bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800/40 disabled:text-slate-500 text-white font-medium px-6 py-2.5 rounded-lg transition-all shadow-lg shadow-indigo-600/10 active:scale-[0.98] h-[42px] flex items-center justify-center min-w-[160px]"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Analyzing...</span>
                </div>
              ) : 'Analyze Repository'}
            </button>
          </div>
        </section>

        {/* Error Alert Display */}
        {error && (
          <div className="bg-rose-950/30 border border-rose-900/50 rounded-xl p-4 text-rose-400 text-sm flex items-center gap-2">
            <span className="font-semibold bg-rose-500/10 px-2 py-0.5 rounded text-xs uppercase tracking-wide">Error</span>
            <span>{error}</span>
          </div>
        )}

        {/* Raw Data Results Box */}
        {data && (
          <section className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
            <div className="border-b border-slate-800 bg-slate-900/80 px-6 py-3 flex items-center justify-between">
              <h3 className="text-xs font-semibold tracking-wide text-slate-400 uppercase">
                Raw Analysis Output
              </h3>
            </div>
            <div className="p-6 bg-slate-950 overflow-x-auto max-h-[550px] border-t border-slate-900">
              <pre className="text-xs font-mono text-emerald-400 leading-relaxed drop-shadow-sm">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;