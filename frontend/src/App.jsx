import { useEffect, useState } from "react";

function App() {
  const [status, setStatus] = useState("Checking backend...");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then((res) => res.json())
      .then((data) => setStatus(JSON.stringify(data)))
      .catch((err) => setStatus("Connection failed: " + err.message));
  }, []);

  return (
    <div style={{ padding: "40px" }}>
      <h1>CinePilot AI</h1>
      <h2>{status}</h2>
    </div>
  );
}

export default App;