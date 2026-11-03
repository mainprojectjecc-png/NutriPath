import { useState } from "react";

export default function SuggestionForm({ onSubmit }) {
  const [text, setText] = useState("");
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(text); setText(""); }}>
      <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Suggest a replacement food" />
      <button type="submit">Send suggestion</button>
    </form>
  );
}