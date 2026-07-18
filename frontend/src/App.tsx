import {useState} from "react";

interface AnalyzeResponse {
    analysis: string;
}

function App() {
    const [cvText, setCvText] = useState("");
    const [jobListing, setJobListing] = useState("");
    const [result, setResult] = useState("");
    const [loading, setLoading] = useState(false);


    const analyze = async () => {
        setLoading(true);
        setResult("");
        try {
            const res = await fetch("http://localhost:8000/analyze", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({cv_text: cvText, job_listing: jobListing}),
            });
            if (!res.ok) {
                const err = await res.json();
                setResult(`Error ${res.status}: ${err.detail}`);
                return;
            }
            const data: AnalyzeResponse = await res.json();
            setResult(data.analysis);
        } catch {
            setResult("Network error — is the backend running?");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <h1>CV Analyzer</h1>
            <p className="subtitle">Paste a CV and a job listing — get an AI match analysis.</p>

            <div className="inputs">
                <div className="field">
                    <label>CV</label>
                    <textarea
                        placeholder="Paste the CV text..."
                        value={cvText}
                        onChange={(e) => setCvText(e.target.value)}
                    />
                </div>
                <div className="field">
                    <label>Job listing</label>
                    <textarea
                        placeholder="Paste the job listing..."
                        value={jobListing}
                        onChange={(e) => setJobListing(e.target.value)}
                    />
                </div>
            </div>

            <button onClick={analyze} disabled={loading || !cvText || !jobListing}>
                {loading ? "Analyzing..." : "Analyze"}
            </button>

            {result && (
                <div className="result">
                    <h2>Analysis</h2>
                    <pre>{result}</pre>
                </div>
            )}
        </div>
    );
}

export default App;