import React, { useState } from "react";
import { postJson } from "../lib/api";

export default function Supervisor() {
  const [approvalText, setApprovalText] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function approve() {
    setBusy(true);
    setErr(null);
    setResult(null);
    try {
      const approval = JSON.parse(approvalText);
      // approval object already contains tool_name, tool_input, ctx from agent-runtime response
      const payload = {
        approved: true,
        tool_name: approval.tool_name,
        tool_input: approval.tool_input,
        ctx: approval.ctx
      };
      const data = await postJson<any>("/approvals/resume", payload);
      setResult(data);
    } catch (e: any) {
      setErr(e?.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <div className="h1">Supervisor</div>
      <div className="small">
        Paste the approval JSON from Nurse page, then Approve (sends to <code>/approvals/resume</code>).
      </div>

      <div style={{ marginTop: 12 }}>
        <div className="label">Approval JSON</div>
        <textarea
          className="textarea"
          placeholder='Paste approval object here (from Nurse response.output.approval)'
          value={approvalText}
          onChange={(e) => setApprovalText(e.target.value)}
        />
      </div>

      <div style={{ marginTop: 12, display: "flex", gap: 10 }}>
        <button className="btn secondary" onClick={approve} disabled={busy}>
          {busy ? "Approving..." : "Approve"}
        </button>
      </div>

      {err && (
        <div style={{ marginTop: 12 }}>
          <div className="label">Error</div>
          <pre>{err}</pre>
        </div>
      )}

      {result && (
        <div style={{ marginTop: 12 }}>
          <div className="label">Result</div>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
