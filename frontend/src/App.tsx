import {useState} from "react";

interface AnalyzeResponse {
    analysis: string;
}

interface StructuredAnalysis {
    score: number;
    matched: string[];
    missing: string[];
    suggestions: string[];
}

class ApiError extends Error {}

function ScoreBadge({score}: { score: number }) {
    const color = score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#ef4444";
    return (
        <div className="score-badge" style={{borderColor: color, color}}>
            <span className="score-number">{score}</span>
            <span className="score-label">/ 100</span>
        </div>
    );
}

function RequirementList({title, items, variant}: { title: string; items: string[]; variant: "good" | "bad" }) {
    if (items == null || items.length === 0) return null;
    return (
        <div className={`req-list ${variant}`}>
            <h3>{title}</h3>
            <ul>
                {items.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
        </div>
    );
}

async function extractErrorMessage(res: Response): Promise<string> {
    const err = await res.json();
    return `Error ${res.status}: ${err.detail}`;
}

async function readStream(res: Response, onChunk: (text: string) => void, onNoBody: () => void) {
    if (!res.body) {
        onNoBody();
        return;
    }
    const decoder = new TextDecoder();
    const reader = res.body.getReader();
    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        onChunk(decoder.decode(value, {stream: true}));
    }
}

function App() {
    const [cvText, setCvText] = useState("");
    const [jobListing, setJobListing] = useState("");
    const [structuredOutput, setStructuredOutput] = useState<Partial<StructuredAnalysis> | null>(null);
    const [result, setResult] = useState("");
    const [loading, setLoading] = useState(false);
    const [provider, setProvider] = useState("anthropic");
    const [stream, setStream] = useState("stream");
    const [structured, setStructured] = useState("structured");
    const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";

    const emptyOutput = () => {
        setLoading(true);
        setResult("");
        setStructuredOutput(null);
    }

    const postAnalyze = async (path: string): Promise<Response> => {
        const res = await fetch(baseURL + path, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({cv_text: cvText, job_listing: jobListing, provider: provider}),
        });
        if (!res.ok) throw new ApiError(await extractErrorMessage(res));
        return res;
    };

    const analyze = async () => {
        emptyOutput();
        try {
            const res = await postAnalyze("/analyze");
            const data: AnalyzeResponse = await res.json();
            setResult(data.analysis);
        } catch (e) {
            setResult(e instanceof ApiError ? e.message : "Network error — is the backend running?");
        } finally {
            setLoading(false);
        }
    };

    const analyzeStructured = async () => {
        emptyOutput();
        try {
            const res = await postAnalyze("/analyze_structured");
            const data: StructuredAnalysis = await res.json();
            setStructuredOutput(data);
        } catch (e) {
            setResult(e instanceof ApiError ? e.message : "Network error — is the backend running?");
        } finally {
            setLoading(false);
        }
    };

    const analyzeStream = async () => {
        emptyOutput();
        try {
            const res = await postAnalyze("/analyze_stream");
            await readStream(
                res,
                text => setResult(prev => prev + text),
                () => setResult("No response body."),
            );
        } catch (e) {
            if (e instanceof ApiError) setResult(e.message);
            else setResult(prev => prev + "\n[connection lost]");
        } finally {
            setLoading(false);
        }
    };

    const analyzeStructuredStream = async () => {
        emptyOutput();
        let buffer = "";
        try {
            const res = await postAnalyze("/analyze_structured_stream");
            await readStream(
                res,
                text => {
                    buffer += text;
                    checkForValidPartsInBuffer(buffer);
                },
                () => setResult("No response body."),
            );
        } catch (e) {
            if (e instanceof ApiError) setResult(e.message);
            else setResult(prev => prev + "\n[connection lost]");
        } finally {
            setLoading(false);
        }
    };

    const checkForValidPartsInBuffer = (buffer: string) => {
        const stack = [];
        let inString = false;
        for (let i = 0; i < buffer.length; i++) {
            const el = buffer[i];
            if (inString) {
                if (el === '"' && buffer[i - 1] !== '\\') inString = false;
            } else {
                if (el === '"') inString = true;
                else if (el === '{' || el === '[') stack.push(el);
                else if (el === '}' || el === ']') stack.pop();
            }
        }

        if (inString) {
            buffer = buffer.substring(0, buffer.lastIndexOf('"'));
        }

        buffer = buffer.trimEnd();
        if (buffer.at(-1) === ':') {
            const lastComma = buffer.lastIndexOf(',');
            const lastBrace = buffer.lastIndexOf('{');
            const cutPoint = Math.max(lastComma, lastBrace);
            buffer = buffer.substring(0, cutPoint);
        }
        buffer = buffer.trimEnd();
        if (buffer.at(-1) === ',') buffer = buffer.slice(0, -1);

        while (stack.length > 0) {
            const el = stack.pop();
            buffer += el === "{" ? "}" : "]";
        }
        try {
            const parsed = JSON.parse(buffer);
            setStructuredOutput(parsed);
        } catch {
            // buffer is still an incomplete JSON fragment — ignore and wait for more chunks
        }
    }

    const uploadCv = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        setLoading(true);
        try {
            const res = await fetch(baseURL + "/upload_cv", {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                setCvText(await extractErrorMessage(res));
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

    const manageQuery = () =>
        stream == "stream" && structured == "structured"
            ? analyzeStructuredStream()
            : stream == "stream" && structured == "notStructured"
                ? analyzeStream()
                : stream == "noStream" && structured == "structured"
                    ? analyzeStructured()
                    : analyze();

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
                <div className="provider-field">
                    <label htmlFor="structured">Output</label>
                    <select
                        id="structured"
                        value={structured}
                        onChange={(e) => setStructured(e.target.value)}
                    >
                        <option value="structured">Structured</option>
                        <option value="notStructured">Not structured</option>
                    </select>
                </div>
                <button onClick={manageQuery}
                        disabled={loading || !cvText || !jobListing}>
                    {loading ? "Analyzing..." : "Analyze"}
                </button>
            </div>

            {result && (
                <div className="result">
                    <h2>Analysis</h2>
                    <pre>{result}</pre>
                </div>
            )}
            {structuredOutput && (
                <div className="result">
                    <h2>Structured Analysis</h2>
                    {structuredOutput.score !== undefined && <ScoreBadge score={structuredOutput.score}/>}
                    <div className="req-columns">
                        <RequirementList title="Matched" items={structuredOutput.matched ?? []} variant="good"/>
                        <RequirementList title="Missing" items={structuredOutput.missing ?? []} variant="bad"/>
                    </div>
                    <RequirementList title="Suggestions" items={structuredOutput.suggestions ?? []} variant="good"/>
                </div>
            )}
        </div>
    );
}

export default App;
