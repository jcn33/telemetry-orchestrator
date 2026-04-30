import { useEffect, useState } from "react";

type ApiHealth = { status: string };

export function App(): JSX.Element {
  const [apiStatus, setApiStatus] = useState<string>("checking...");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json() as Promise<ApiHealth>)
      .then((data) => setApiStatus(data.status))
      .catch((err: Error) => setApiStatus(`error: ${err.message}`));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>telemetry-orchestrator</h1>
      <p>API health: <strong>{apiStatus}</strong></p>
    </main>
  );
}
