import { useState } from "react";

export default function SuggestionForm({ onSubmit, disabled }) {
  const [text, setText] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    onSubmit(text.trim());
    setText("");
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Suggest a replacement food"
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !text.trim()}>
        Send suggestion
      </button>
    </form>
  );
}