import { useState, useEffect } from "react";
import { assistantApi } from "../api";

interface Props {
  projectId: number;
}

export default function AssistantChat({ projectId }: Props) {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    assistantApi.messages(projectId).then((msgs) =>
      setMessages(msgs.map((m) => ({ role: m.role, content: m.content })))
    );
  }, [projectId]);

  const send = async () => {
    if (!input.trim()) return;
    setLoading(true);
    const userMsg = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    try {
      const reply = await assistantApi.chat(projectId, userMsg);
      setMessages((prev) => [...prev, { role: "assistant", content: reply.content }]);
    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Failed"}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Project AI Assistant</h3>
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            <strong>{m.role === "user" ? "You" : "Assistant"}:</strong> {m.content}
          </div>
        ))}
      </div>
      <div className="actions">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about tasks, architecture, dependencies..."
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button className="btn-primary" onClick={send} disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
}
