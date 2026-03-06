import React, { useMemo, useRef, useState } from "react";
import { postJson } from "../lib/api";

type InvocationOk = { ok: true; output: any; correlation_id: string };
type InvocationErr = { ok: false; error: { code: string; message: string }; correlation_id?: string };
type InvocationResp = InvocationOk | InvocationErr;

type ChatMsg = {
  id: string;
  role: "user" | "assistant" | "system";
  text: string;
  ts: number;
};

function uid() {
  return Math.random().toString(16).slice(2) + "-" + Date.now().toString(16);
}

function extractAssistantText(output: any): string {
  // Your backend now returns: { output: { answer: "..." } }
  if (!output) return "No output.";

  if (typeof output === "string") return output;

  if (typeof output?.answer === "string") return output.answer;

  // If something regresses to TWO_STEP dict:
  if (output?.result === "OK" && output?.mode === "TWO_STEP") {
    const nurse = (output?.nurse_summary || "").trim();
    const policy = (output?.policy_summary || "").trim();
    return [nurse, policy].filter(Boolean).join("\n\n") || "Done.";
  }

  // Approval required dict (some flows might return this)
  if (output?.result === "APPROVAL_REQUIRED") {
    const a = output?.approval || {};
    const tool = a?.tool_name || "unknown_tool";
    const msg = a?.message || "Approval required.";
    return `Approval required.\nTool: ${tool}\nReason: ${msg}`;
  }

  // Fallback
  return JSON.stringify(output, null, 2);
}

export default function Nurse() {
  const [tenantId, setTenantId] = useState("t1");
  const [userId, setUserId] = useState("u1");
  const [threadId, setThreadId] = useState("th-1");

  const [input, setInput] = useState("For assessment asmt-000001 summarize status and latest note");
  const [busy, setBusy] = useState(false);

  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      id: uid(),
      role: "assistant",
      ts: Date.now(),
      text:
        "Hi — I’m the Nurse assistant.\n\nTry:\n- For assessment asmt-000001 summarize status and latest note\n- Write a case note for assessment asmt-000001: <text>",
    },
  ]);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  function scrollToBottom() {
    requestAnimationFrame(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }));
  }

  const lastApprovalPayload = useMemo(() => {
    // If your UI wants to copy approval JSON, we can store it when backend returns it.
    // For now, we’ll detect it from the latest assistant message text only if backend returns approval object.
    return null as null | string;
  }, []);

  async function send() {
    const prompt = (input || "").trim();
    if (!prompt || busy) return;

    const userMsg: ChatMsg = { id: uid(), role: "user", ts: Date.now(), text: prompt };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setBusy(true);
    scrollToBottom();

    try {
      const data = await postJson<InvocationResp>("/invocations", {
        prompt,
        tenant_id: tenantId,
        user_id: userId,
        thread_id: threadId,
      });

      if (!data.ok) {
        const errText = `Error (${data.error.code}): ${data.error.message}`;
        setMessages((m) => [...m, { id: uid(), role: "system", ts: Date.now(), text: errText }]);
        scrollToBottom();
        return;
      }

      const assistantText = extractAssistantText(data.output);

      setMessages((m) => [
        ...m,
        { id: uid(), role: "assistant", ts: Date.now(), text: assistantText },
      ]);
      scrollToBottom();
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { id: uid(), role: "system", ts: Date.now(), text: `UI Error: ${e?.message || String(e)}` },
      ]);
      scrollToBottom();
    } finally {
      setBusy(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends, Shift+Enter adds newline
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", height: "78vh" }}>
      <div className="row" style={{ alignItems: "center", justifyContent: "space-between" }}>
        <div className="h1">Nurse Chat</div>
        <div className="small" style={{ opacity: 0.8 }}>
          thread_id=<code>{threadId}</code>
        </div>
      </div>

      {/* Header controls */}
      <div className="row" style={{ marginTop: 10 }}>
        <div className="col">
          <div className="label">tenant_id</div>
          <input className="input" value={tenantId} onChange={(e) => setTenantId(e.target.value)} />
        </div>
        <div className="col">
          <div className="label">user_id</div>
          <input className="input" value={userId} onChange={(e) => setUserId(e.target.value)} />
        </div>
        <div className="col">
          <div className="label">thread_id</div>
          <input className="input" value={threadId} onChange={(e) => setThreadId(e.target.value)} />
        </div>
      </div>

      {/* Chat transcript */}
      <div
        style={{
          flex: 1,
          marginTop: 12,
          padding: 12,
          border: "1px solid rgba(255,255,255,0.12)",
          borderRadius: 10,
          overflowY: "auto",
          background: "#0f172a",
          minHeight: "360px",
          maxHeight: "420px"
        }}
      >
        {messages.map((m) => {
          const isUser = m.role === "user";
          const isSystem = m.role === "system";
          return (
            <div
              key={m.id}
              style={{
                display: "flex",
                justifyContent: isUser ? "flex-end" : "flex-start",
                marginBottom: 10,
              }}
            >
            <div
              style={{
                maxWidth: "78%",
                whiteSpace: "pre-wrap",
                padding: "10px 12px",
                borderRadius: 12,
                border: isSystem
                  ? "1px solid rgba(239,68,68,0.45)"
                  : isUser
                  ? "1px solid rgba(59,130,246,0.45)"
                  : "1px solid rgba(255,255,255,0.12)",
                background: isSystem
                  ? "#3f1d1d"
                  : isUser
                  ? "#1d4ed8"
                  : "#1e293b",
                color: "#f8fafc",
                fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
                fontSize: 14,
                lineHeight: 1.45,
                boxShadow: "0 1px 2px rgba(0,0,0,0.25)"
              }}
            >
                {m.text}
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {/* Composer */}
      <div style={{ marginTop: 12 }}>
        <div className="label">Message</div>
        <textarea
          className="textarea"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Type message... (Enter to send, Shift+Enter for newline)"
          style={{
            minHeight: 70,
            background: "#0f172a",
            color: "#f8fafc",
            border: "1px solid rgba(255,255,255,0.12)"
          }}
        />
        <div style={{ marginTop: 10, display: "flex", gap: 10 }}>
          <button className="btn" onClick={send} disabled={busy}>
            {busy ? "Sending..." : "Send"}
          </button>

          <button
            className="btn secondary"
            onClick={() => setMessages([{ id: uid(), role: "assistant", ts: Date.now(), text: "New chat. Ask me anything." }])}
            disabled={busy}
          >
            Clear chat
          </button>
        </div>
      </div>

      {/* Optional: approval payload hook later */}
      {lastApprovalPayload ? null : null}
    </div>
  );
}