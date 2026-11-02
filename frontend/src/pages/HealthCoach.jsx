
import { useState } from "react";
import {
  HeartPulse, Send, CheckCircle2, Clock,
  MessageCircle, Leaf, ThumbsUp
} from "lucide-react";

export default function HealthCoach() {
  const [requests, setRequests] = useState([]);
  const [food, setFood] = useState("");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState("");

  const [messages, setMessages] = useState([
    {
      from: "coach",
      text: "Hello! Welcome to NutriPath. How can I support your healthy journey today?"
    }
  ]);

  function submitRequest(e) {
    e.preventDefault();

    if (!food.trim() || !reason) {
      setMessage("Please enter the food and select a reason.");
      return;
    }

    setRequests(prev => [
      ...prev,
      {
        id: Date.now(),
        food,
        suggestion: "Awaiting coach suggestion",
        status: "Pending"
      }
    ]);

    setMessage("Your request is saved for this session only; it has not been sent to a coach.");
    setFood("");
    setReason("");
  }

  function acceptSuggestion(id) {
    setRequests(prev =>
      prev.map(item =>
        item.id === id
          ? { ...item, status: "Accepted" }
          : item
      )
    );
  }

  function sendMessage(e) {
    e.preventDefault();

    if (!chat.trim()) return;

    setMessages(prev => [
      ...prev,
      { from: "user", text: chat },
      {
        from: "coach",
        text: "Thank you for sharing! This is a demo response. Personalized coach suggestions will be connected to the backend."
      }
    ]);

    setChat("");
  }

  return (
    <>
      <div className="page-title-row">
        <div>
          <span className="eyebrow">PERSONALIZED WELLNESS SUPPORT</span>
          <h1>Health Coach</h1>
          <p>Get guidance and make healthier everyday choices.</p>
        </div>
        <span className="online-label">
          <span className="online-dot"></span> Demo mode
        </span>
      </div>

      <section className="coach-banner">
        <div className="coach-icon">
          <HeartPulse size={35} />
        </div>
        <div>
          <h2>Your wellness companion</h2>
          <p>Explore food alternatives, review suggestions and manage your requests.</p>
        </div>
        <div className="coach-leaf">🌿</div>
      </section>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h3>Food replacement request</h3>
              <p>Tell us what food you want to replace.</p>
            </div>
            <Leaf size={22} />
          </div>

          <form className="request-form" onSubmit={submitRequest}>
            <label>Food item</label>
            <input
              value={food}
              onChange={e => setFood(e.target.value)}
              placeholder="Enter food name..."
            />

            <label>Reason</label>
            <select
              value={reason}
              onChange={e => setReason(e.target.value)}
            >
              <option value="">Select reason</option>
              <option>Food preference</option>
              <option>Allergy or intolerance</option>
              <option>Food not available</option>
              <option>Other</option>
            </select>

            <button className="primary-button" type="submit">
              <Send size={16} /> Submit request
            </button>

            {message && <p className="form-message">{message}</p>}
          </form>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <h3>Request summary</h3>
              <p>Track your food replacement requests.</p>
            </div>
            <HeartPulse size={22} />
          </div>

          <div className="request-stats">
            <div>
              <strong>{requests.length}</strong>
              <span>Total</span>
            </div>
            <div>
              <strong>{requests.filter(r => r.status === "Pending").length}</strong>
              <span>Pending</span>
            </div>
            <div>
              <strong>{requests.filter(r => r.status === "Accepted").length}</strong>
              <span>Accepted</span>
            </div>
          </div>
        </section>
      </div>

      <section className="panel requests-panel">
        <div className="panel-heading">
          <div>
            <h3>My requests and suggestions</h3>
            <p>Review your alternatives and their current status.</p>
          </div>
        </div>

        {requests.map(item => (
          <div className="request-row" key={item.id}>
            <div className="request-food-icon">🥗</div>

            <div className="request-info">
              <strong>{item.food}</strong>
              <span>Suggested alternative: {item.suggestion}</span>
            </div>

            <div className="request-actions">
              <span className={`status ${item.status.toLowerCase()}`}>
                {item.status === "Accepted" ? (
                  <CheckCircle2 size={14} />
                ) : (
                  <Clock size={14} />
                )}
                {item.status}
              </span>

              {item.status === "Suggested" && (
                <button
                  className="small-button"
                  onClick={() => acceptSuggestion(item.id)}
                >
                  <ThumbsUp size={14} /> Accept
                </button>
              )}
            </div>
          </div>
        ))}
      </section>

      <section className="panel chat-panel">
        <div className="panel-heading">
          <div>
            <h3><MessageCircle size={19} /> NutriPath Assistant</h3>
            <p>Demo conversation interface</p>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map((item, index) => (
            <div
              key={index}
              className={`chat-message ${item.from}`}
            >
              {item.text}
            </div>
          ))}
        </div>

        <form className="chat-input" onSubmit={sendMessage}>
          <input
            value={chat}
            onChange={e => setChat(e.target.value)}
            placeholder="Ask about healthy food choices..."
          />
          <button className="primary-button" type="submit">
            <Send size={17} />
          </button>
        </form>
      </section>
    </>
  );
}
