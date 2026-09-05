import { useState, useEffect, useRef, useMemo } from "react";
import { createRun, getRunStatus, getRunArtifacts } from "./api";
import "./App.css";

const POLL_INTERVAL_MS = 3000;

export default function App() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/pallets/itsdangerous");
  const [run, setRun] = useState(null); // { run_id, status, ... }
  const [artifacts, setArtifacts] = useState([]);
  const [selectedArtifact, setSelectedArtifact] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [clock, setClock] = useState("00:00");

  const pollRef = useRef(null);

  useEffect(() => {
    return () => clearInterval(pollRef.current); // cleanup on unmount
  }, []);

  useEffect(() => {
    const tick = () => {
      const d = new Date();
      setClock(`${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`);
    };
    tick();
    const id = setInterval(tick, 15000);
    return () => clearInterval(id);
  }, []);

  // The backend has occasionally returned the same ADR twice in one run.
  // Dedupe defensively on the frontend so it never shows duplicate rows,
  // while the real fix (not emitting dupes) should happen server-side.
  const uniqueArtifacts = useMemo(() => {
    const seen = new Set();
    return artifacts.filter((a, i) => {
      const key = a.id ?? `${a.title}::${a.content}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }, [artifacts]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setArtifacts([]);
    setSelectedArtifact(null);
    setSubmitting(true);

    try {
      const newRun = await createRun(repoUrl);
      setRun(newRun);
      startPolling(newRun.run_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  function startPolling(runId) {
    clearInterval(pollRef.current);

    pollRef.current = setInterval(async () => {
      try {
        const updated = await getRunStatus(runId);
        setRun(updated);

        if (updated.status === "completed") {
          clearInterval(pollRef.current);
          const docs = await getRunArtifacts(runId);
          setArtifacts(docs);
        } else if (updated.status === "failed") {
          clearInterval(pollRef.current);
          setError(updated.error || "Run failed");
        }
      } catch (err) {
        clearInterval(pollRef.current);
        setError(err.message);
      }
    }, POLL_INTERVAL_MS);
  }

  const isBusy = run?.status === "pending" || run?.status === "processing";

  // Sources sometimes arrive as a mix of proper "commit#Lline" strings and
  // bare numbers (line numbers that didn't get merged into the hash on the
  // backend). Render whatever comes through without crashing or leaving
  // stray empty tags, and merge a trailing bare number into the previous tag
  // when it looks like a split commit/line pair.
  function formatSources(sources) {
    const cleaned = (sources || []).filter((s) => s !== null && s !== undefined && s !== "");
    const merged = [];
    for (const s of cleaned) {
      const str = String(s);
      const isBareNumber = /^\d+$/.test(str);
      if (isBareNumber && merged.length > 0 && !/#L\d+$/.test(merged[merged.length - 1])) {
        merged[merged.length - 1] = `${merged[merged.length - 1]}#L${str}`;
      } else {
        merged.push(str);
      }
    }
    return merged;
  }

  return (
    <div className="desktop">
      <div className="desktop-icons">
        <div className="dicon">
          <div className="glyph"></div>
          <span>repo.git</span>
        </div>
        <div className="dicon">
          <div className="glyph"></div>
          <span>adr_output</span>
        </div>
      </div>

      <div className="window raised">
        <div className="titlebar">
          <div className="titlebar-left">
            <div className="app-icon"></div>
            <span className="titlebar-label">AI-Enhanced Documentation Generator</span>
          </div>
          <div className="win-buttons">
            <span className="winbtn raised">_</span>
            <span className="winbtn raised">&#9633;</span>
            <span className="winbtn raised">X</span>
          </div>
        </div>

        <div className="menubar">
          <span>File</span>
          <span>Edit</span>
          <span>Run</span>
          <span>View</span>
          <span>Help</span>
        </div>

        <div className="toolbar">
          <div className="toolbtn raised">&#9654;</div>
          <div className="toolbtn raised">&#9724;</div>
          <div className="toolbtn raised">&#8635;</div>
          <div className="tsep"></div>
          <div className="toolbtn raised">&#128193;</div>
        </div>

        <div className="content">
          <div className="groupbox sunken">
            <span className="groupbox-label">Target repository</span>
            <form onSubmit={handleSubmit} className="control-row">
              <label>repo_url:</label>
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                disabled={submitting || isBusy}
              />
              <button className="run-btn raised" type="submit" disabled={submitting || isBusy}>
                {submitting ? "Starting..." : "Generate docs"}
              </button>
            </form>
          </div>

          {error && (
            <div className="alert-box sunken">
              <span className="alert-icon">!</span>
              <span>{error}</span>
            </div>
          )}

          {run && (
            <div className="groupbox sunken">
              <span className="groupbox-label">synthesis.exe — status</span>
              <div className="konsole">
                &gt; status: {run.status}
                {isBusy && <span className="cursor">&nbsp;</span>}
              </div>
              {isBusy && (
                <div className="bar-track">
                  <div className="sunken-inner">
                    {Array.from({ length: 20 }).map((_, i) => (
                      <div
                        key={i}
                        className="block block-scan"
                        style={{ animationDelay: `${i * 0.06}s` }}
                      ></div>
                    ))}
                  </div>
                </div>
              )}
              {isBusy && <div className="bay-status">analyzing repo, this can take a minute...</div>}
            </div>
          )}

          {uniqueArtifacts.length > 0 && (
            <div className="groupbox sunken">
              <span className="groupbox-label">/output/adrs ({uniqueArtifacts.length})</span>
              <div className="results">
                <div className="listview">
                  {uniqueArtifacts.map((a, i) => (
                    <div
                      key={a.id ?? `${a.title}-${i}`}
                      className={`listrow ${selectedArtifact?.id === a.id ? "active" : ""}`}
                      onClick={() => setSelectedArtifact(a)}
                    >
                      <div className="row-icon"></div>
                      <div className="row-text">
                        <div className="row-name">{a.title}</div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="detail-panel sunken">
                  {selectedArtifact ? (
                    <>
                      <div className="detail-title">{selectedArtifact.title}</div>
                      <pre className="detail-content">{selectedArtifact.content}</pre>
                      <div className="detail-sources">
                        <span className="detail-sources-label">Sources</span>
                        <div className="dialog-tags">
                          {formatSources(selectedArtifact.sources).map((s, i) => (
                            <span className="dialog-tag" key={i}>
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    </>
                  ) : (
                    <p className="placeholder">Select an ADR to view its full content and sources.</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="statusbar">
          <span>{isBusy ? "Running..." : error ? "Failed." : "Ready."}</span>
          <span>{run ? `${repoUrl}` : "no run yet"}</span>
        </div>
      </div>

      <div className="taskbar">
        <div className="kbtn raised">
          <div className="gear"></div>
          <span>K</span>
        </div>
        <div className="pager raised">
          <div className="pcell active"></div>
          <div className="pcell"></div>
          <div className="pcell"></div>
          <div className="pcell"></div>
        </div>
        <div className="taskitem sunken">
          <div className="app-icon"></div>
          <span>AI-Enhanced Documentation Generator</span>
        </div>
        <div className="tray raised">&#9993; &#128266;</div>
        <div className="clock raised">{clock}</div>
      </div>
    </div>
  );
}