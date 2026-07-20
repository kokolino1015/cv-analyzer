import {useState} from "react";

interface AnalyzeResponse {
    analysis: string;
}

function App() {
    const [cvText, setCvText] = useState("");
    const [jobListing, setJobListing] = useState("");
    const [result, setResult] = useState("");
    const [loading, setLoading] = useState(false);
    const [provider, setProvider] = useState("anthropic");
    const [stream, setStream] = useState("stream");

    const analyze = async () => {
        setLoading(true);
        setResult("");
        try {
            const res = await fetch("http://localhost:8000/analyze", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({cv_text: cvText, job_listing: jobListing, provider: provider}),
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

    const analyze_stream = async () => {
        setLoading(true);
        setResult("");
        try {
            const res = await fetch("http://localhost:8000/analyze_stream", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({cv_text: cvText, job_listing: jobListing, provider: provider}),
            });

            if (!res.ok) {
                const err = await res.json();
                setResult(`Error ${res.status}: ${err.detail}`);
                return;
            }

            if (!res.body) {
                setResult("No response body.");
                return;
            }

            const decoder = new TextDecoder();
            let reader = res.body?.getReader();

            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                let text = decoder.decode(value, {stream: true})
                setResult(prev => prev + text);
            }
        } catch {
            setResult(prev => prev + "\n[connection lost]")
        } finally {
            setLoading(false);
        }
    };

    const uploadCv = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        setLoading(true);
        try {
            const res = await fetch("http://localhost:8000/upload_cv", {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                const err = await res.json();
                setCvText(`Error ${res.status}: ${err.detail}`);
                return;
            }
            const data: { text: string } = await res.json();
            setCvText(data.text);
        } catch {
            setCvText("Network error — is the backend running?");
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
                    <input type="file" id="cv-file" accept=".pdf" onChange={uploadCv} hidden/>
                    <label htmlFor="cv-file" className="file-btn">
                        📄 Upload PDF
                    </label>
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

            <div className="controls">
                <div className="provider-field">
                    <label htmlFor="provider">Provider</label>
                    <select
                        id="provider"
                        value={provider}
                        onChange={(e) => setProvider(e.target.value)}
                    >
                        <option value="anthropic">Claude (Anthropic)</option>
                        <option value="ollama">Local (Ollama)</option>
                    </select>
                </div>
                <div className="provider-field">
                    <label htmlFor="stream">Stream</label>
                    <select
                        id="stream"
                        value={stream}
                        onChange={(e) => setStream(e.target.value)}
                    >
                        <option value="stream">Stream</option>
                        <option value="noStream">No stream</option>
                    </select>
                </div>
                <button onClick={stream == "stream" ? analyze_stream : analyze} disabled={loading || !cvText || !jobListing || !stream}>
                    {loading ? "Analyzing..." : "Analyze"}
                </button>
            </div>

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