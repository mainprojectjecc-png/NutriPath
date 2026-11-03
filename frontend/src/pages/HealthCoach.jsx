import { useEffect, useState } from "react";
import {
  HeartPulse, Send, CheckCircle2, Clock,
  MessageCircle, Leaf, ThumbsDown, ThumbsUp
} from "lucide-react";
import {
  acceptFoodReplacementSuggestion,
  createFoodReplacementRequest,
  getActiveFoods,
  getCoachRequests,
  getFoodReplacementRequests,
  getNutritionData,
  rejectFoodReplacementSuggestion,
  submitCoachSuggestion
} from "../services/nutrition";

function requestFoodName(request) {
  return request.NutritionLog?.food_name ||
    request.MealItem?.Food?.FoodName ||
    request.RequestedFood?.FoodName ||
    "Food not available";
}

function requestStatus(request) {
  if (request.Suggestion?.Status === "Pending" && request.Status === "Reviewed") {
    return "Suggested";
  }
  return request.Status;
}

function statusClass(status) {
  if (status === "Reviewed" || status === "Suggested" || status === "Rejected") {
    return "suggested";
  }
  return status.toLowerCase();
}

export default function HealthCoach({ user }) {
  const role = typeof user?.role === "string" ? user.role.trim().toLowerCase() : "";
  const isCoach = role === "coach";
  const isUser = role === "user";

  const [requests, setRequests] = useState([]);
  const [meals, setMeals] = useState([]);
  const [foods, setFoods] = useState([]);
  const [selectedMealId, setSelectedMealId] = useState("");
  const [selectedRequestId, setSelectedRequestId] = useState("");
  const [suggestedFoodId, setSuggestedFoodId] = useState("");
  const [reason, setReason] = useState("");
  const [suggestionMessage, setSuggestionMessage] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function loadData() {
    if (!user || (!isCoach && !isUser)) return;

    setLoading(true);
    setError("");
    try {
      if (isCoach) {
        const [coachRequests, activeFoods] = await Promise.all([
          getCoachRequests(),
          getActiveFoods()
        ]);
        setRequests(coachRequests);
        setFoods(activeFoods);
        const pendingRequests = coachRequests.filter(
          request => request.Status === "Pending"
        );
        setSelectedRequestId(current =>
          pendingRequests.some(request => String(request.RequestID) === current)
            ? current
            : pendingRequests.length
              ? String(pendingRequests[0].RequestID)
              : ""
        );
      } else if (isUser) {
        const [nutrition, userRequests] = await Promise.all([
          getNutritionData(user.id),
          getFoodReplacementRequests()
        ]);
        setMeals(nutrition.meals);
        setRequests(userRequests);
      }
    } catch (loadError) {
      setError(loadError.message || "Unable to load your coach data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (user) loadData();
  }, [user?.id, isCoach]);

  async function handleRequest(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!selectedMealId || !reason) {
      setError("Select a meal and a reason.");
      return;
    }

    try {
      setSubmitting(true);
      await createFoodReplacementRequest(Number(selectedMealId), reason);
      setMessage("Your request was sent to the coach.");
      setSelectedMealId("");
      setReason("");
      await loadData();
    } catch (requestError) {
      setError(requestError.message || "Request failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSuggestion(e) {
    e.preventDefault();
    setMessage("");
    setError("");

    const foodId = Number(suggestedFoodId);
    const requestId = Number(selectedRequestId);
    if (!Number.isInteger(requestId) || requestId <= 0 ||
      !Number.isInteger(foodId) || foodId <= 0) {
      setError("Select a request and an active food.");
      return;
    }

    try {
      setSubmitting(true);
      await submitCoachSuggestion(
        requestId,
        foodId,
        suggestionMessage
      );
      setMessage(`Suggestion submitted for request #${requestId}.`);
      setSuggestedFoodId("");
      setSuggestionMessage("");
      await loadData();
    } catch (suggestionError) {
      setError(suggestionError.message || "Suggestion failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleAcceptSuggestion(requestId) {
    setMessage("");
    setError("");
    try {
      setSubmitting(true);
      await acceptFoodReplacementSuggestion(requestId);
      setMessage("The suggested replacement was accepted.");
      await loadData();
    } catch (acceptError) {
      setError(acceptError.message || "Could not accept this suggestion.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleRejectSuggestion(requestId) {
    setMessage("");
    setError("");
    try {
      setSubmitting(true);
      await rejectFoodReplacementSuggestion(requestId);
      setMessage("The suggested replacement was rejected.");
      await loadData();
    } catch (rejectError) {
      setError(rejectError.message || "Could not reject this suggestion.");
    } finally {
      setSubmitting(false);
    }
  }

  const pendingCount = requests.filter(request => request.Status === "Pending").length;
  const reviewedRequests = isCoach
    ? requests.filter(request => request.Status === "Reviewed")
    : [];
  const resolvedRequests = isCoach
    ? requests.filter(request => request.Status === "Accepted" || request.Status === "Rejected")
    : [];
  const pendingRequests = isCoach
    ? requests.filter(request => request.Status === "Pending")
    : requests;
  const suggestionsCount = requests.filter(
    request => request.Suggestion?.Status === "Pending"
  ).length;

  if (!isCoach && !isUser) {
    return <p className="form-message" role="alert">A valid User or Coach role is required.</p>;
  }

  return (
    <>
      <div className="page-title-row">
        <div>
          <span className="eyebrow">
            {isCoach ? "COACH REQUEST MANAGEMENT" : "PERSONALIZED WELLNESS SUPPORT"}
          </span>
          <h1>{isCoach ? "Coach Dashboard" : "My Health Coach"}</h1>
          <p>
            {isCoach
              ? "Review member requests and suggest suitable food alternatives."
              : "Get guidance and make healthier everyday choices."}
          </p>
        </div>
        <span className="online-label">
          <span className="online-dot"></span>
          {isCoach ? "Coach view" : "Connected"}
        </span>
      </div>

      <section className="coach-banner">
        <div className="coach-icon">
          <HeartPulse size={35} />
        </div>
        <div>
          <h2>{isCoach ? "Member food requests" : "Your wellness companion"}</h2>
          <p>
            {isCoach
              ? "Review pending requests and send personalized food suggestions."
              : "Explore food alternatives, review suggestions and manage your requests."}
          </p>
        </div>
        <div className="coach-leaf">🌿</div>
      </section>

      {(message || error) && (
        <p className="form-message" role={error ? "alert" : "status"}>
          {error || message}
        </p>
      )}
      {loading && <p className="form-message" role="status">Loading your latest data...</p>}

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <h3>{isCoach ? "Review pending requests" : "Food replacement request"}</h3>
              <p>
                {isCoach
                  ? "Choose a pending request and an active food from the catalog."
                  : "Tell us what food you want to replace."}
              </p>
            </div>
            <Leaf size={22} />
          </div>

          {isCoach ? (
            <form className="request-form" onSubmit={handleSuggestion}>
              <label htmlFor="coach-request">Request to review</label>
              <select
                id="coach-request"
                value={selectedRequestId}
                onChange={e => setSelectedRequestId(e.target.value)}
                required
              >
                <option value="">Select a pending request</option>
                {pendingRequests.map(request => (
                  <option key={request.RequestID} value={request.RequestID}>
                    #{request.RequestID} · {requestFoodName(request)}
                  </option>
                ))}
              </select>

              <label htmlFor="suggested-food">Suggested food</label>
              <select
                id="suggested-food"
                value={suggestedFoodId}
                onChange={e => setSuggestedFoodId(e.target.value)}
                required
              >
                <option value="">Select an active food</option>
                {foods.map(food => (
                  <option key={food.FoodID} value={food.FoodID}>
                    {food.FoodName} (ID: {food.FoodID})
                  </option>
                ))}
              </select>

              <label htmlFor="suggestion-message">Message to user</label>
              <input
                id="suggestion-message"
                value={suggestionMessage}
                onChange={e => setSuggestionMessage(e.target.value)}
                placeholder="Explain your food suggestion..."
              />

              <button
                className="primary-button"
                type="submit"
                disabled={submitting || pendingRequests.length === 0 || foods.length === 0}
              >
                <Send size={16} />
                {submitting ? "Submitting..." : "Submit suggestion"}
              </button>
            </form>
          ) : (
            <form className="request-form" onSubmit={handleRequest}>
              <label htmlFor="replacement-meal">Food item</label>
              <select
                id="replacement-meal"
                value={selectedMealId}
                onChange={e => setSelectedMealId(e.target.value)}
                required
              >
                <option value="">Select a logged meal</option>
                {meals.map(meal => (
                  <option key={meal.id} value={meal.id}>
                    {meal.foodName} - {meal.mealType} ({meal.date})
                  </option>
                ))}
              </select>

              <label htmlFor="replacement-reason">Reason</label>
              <select
                id="replacement-reason"
                value={reason}
                onChange={e => setReason(e.target.value)}
                required
              >
                <option value="">Select reason</option>
                <option>Food preference</option>
                <option>Allergy or intolerance</option>
                <option>Food not available</option>
                <option>Other</option>
              </select>

              <button
                className="primary-button"
                type="submit"
                disabled={submitting || meals.length === 0}
              >
                <Send size={16} />
                {submitting ? "Submitting..." : "Submit request"}
              </button>

              {meals.length === 0 && !loading && (
                <p className="form-message">Log a meal before requesting a replacement.</p>
              )}
            </form>
          )}
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <h3>{isCoach ? "Coach queue" : "My request summary"}</h3>
              <p>
                {isCoach
                  ? "Live pending work and previously reviewed requests."
                  : "Your personal request and suggestion status."}
              </p>
            </div>
            <HeartPulse size={22} />
          </div>

          <div className="request-stats">
            <div>
              <strong>{isCoach ? pendingCount : requests.length}</strong>
              <span>{isCoach ? "Pending" : "Total"}</span>
            </div>
            <div>
              <strong>{isCoach ? reviewedRequests.length : pendingCount}</strong>
              <span>{isCoach ? "Reviewed this session" : "Pending"}</span>
            </div>
            <div>
              <strong>{isCoach ? foods.length : suggestionsCount}</strong>
              <span>{isCoach ? "Active foods" : "Suggestions"}</span>
            </div>
          </div>
        </section>
      </div>

      <section className="panel requests-panel">
        <div className="panel-heading">
          <div>
            <h3>{isCoach ? "Pending Food Replacement Requests" : "My requests and suggestions"}</h3>
            <p>
              {isCoach
                ? "Review requester details, food, reason and request status."
                : "Review your alternatives and their current status."}
            </p>
          </div>
        </div>

        {pendingRequests.length === 0 && !loading && (
          <p className="form-message">
            {isCoach ? "No pending requests at the moment." : "You have no food replacement requests yet."}
          </p>
        )}

        {pendingRequests.map(request => {
          const status = requestStatus(request);
          const suggestedFood = request.Suggestion?.SuggestedFood?.FoodName;
          const canAccept = !isCoach && request.Suggestion?.Status === "Pending";

          return (
            <div className="request-row" key={request.RequestID}>
              <div className="request-food-icon">🥗</div>

              <div className="request-info">
                <strong>
                  {isCoach
                    ? `Request #${request.RequestID}: ${requestFoodName(request)}`
                    : requestFoodName(request)}
                </strong>
                {isCoach && request.RequestedFood?.FoodName && (
                  <span>Requested alternative: {request.RequestedFood.FoodName}</span>
                )}
                {isCoach && request.User?.FullName && (
                  <span>Requested by: {request.User.FullName}</span>
                )}
                <span>Reason: {request.Reason || "Not provided"}</span>
                {!isCoach && (
                  <span>
                    Suggested alternative: {suggestedFood || "Awaiting coach suggestion"}
                    {request.Suggestion?.Message ? ` · ${request.Suggestion.Message}` : ""}
                  </span>
                )}
              </div>

              <div className="request-actions">
                <span className={`status ${statusClass(status)}`}>
                  {status === "Accepted" ? (
                    <CheckCircle2 size={14} />
                  ) : (
                    <Clock size={14} />
                  )}
                  {status}
                </span>

                {isCoach && (
                  <button
                    className="small-button"
                    type="button"
                    onClick={() => setSelectedRequestId(String(request.RequestID))}
                  >
                    Review
                  </button>
                )}

                {canAccept && (
                  <>
                    <button
                      className="small-button"
                      type="button"
                      disabled={submitting}
                      onClick={() => handleAcceptSuggestion(request.RequestID)}
                    >
                      <ThumbsUp size={14} /> Accept
                    </button>
                    <button
                      className="small-button"
                      type="button"
                      disabled={submitting}
                      onClick={() => handleRejectSuggestion(request.RequestID)}
                    >
                      <ThumbsDown size={14} /> Reject
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}

        {isCoach && reviewedRequests.length > 0 && (
          <>
            <div className="panel-heading">
              <div>
                <h3>Reviewed Requests</h3>
                <p>Requests waiting for the member's response.</p>
              </div>
            </div>
            {reviewedRequests.map(request => (
              <div className="request-row" key={request.RequestID}>
                <div className="request-food-icon">🥗</div>
                <div className="request-info">
                  <strong>
                    Request #{request.RequestID}: {requestFoodName(request)}
                  </strong>
                  {request.User?.FullName && (
                    <span>Requested by: {request.User.FullName}</span>
                  )}
                  <span>Reason: {request.Reason || "Not provided"}</span>
                  <span>
                    Suggested alternative: {request.Suggestion?.SuggestedFood?.FoodName || "Unavailable"}
                    {request.Suggestion?.Message ? ` · ${request.Suggestion.Message}` : ""}
                  </span>
                </div>
                <div className="request-actions">
                  <span className={`status ${statusClass(request.Status)}`}>
                    <CheckCircle2 size={14} />
                    {request.Status}
                  </span>
                </div>
              </div>
            ))}
          </>
        )}
        {isCoach && resolvedRequests.length > 0 && (
          <>
            <div className="panel-heading">
              <div>
                <h3>Resolved Requests</h3>
                <p>Requests accepted or rejected by members.</p>
              </div>
            </div>
            {resolvedRequests.map(request => (
              <div className="request-row" key={request.RequestID}>
                <div className="request-food-icon">🥗</div>
                <div className="request-info">
                  <strong>
                    Request #{request.RequestID}: {requestFoodName(request)}
                  </strong>
                  {request.User?.FullName && (
                    <span>Requested by: {request.User.FullName}</span>
                  )}
                  <span>Reason: {request.Reason || "Not provided"}</span>
                  <span>
                    Suggested alternative: {request.Suggestion?.SuggestedFood?.FoodName || "Unavailable"}
                    {request.Suggestion?.Message ? ` · ${request.Suggestion.Message}` : ""}
                  </span>
                </div>
                <div className="request-actions">
                  <span className={`status ${statusClass(request.Status)}`}>
                    <CheckCircle2 size={14} />
                    {request.Status}
                  </span>
                </div>
              </div>
            ))}
          </>
        )}
      </section>

      <section className="panel chat-panel">
        <div className="panel-heading">
          <div>
            <h3><MessageCircle size={19} /> NutriPath Assistant</h3>
            <p>Direct chat is not connected yet</p>
          </div>
        </div>

        <div className="chat-messages">
          <div className="chat-message coach">
            Use a food replacement request to contact your coach. Direct messaging is currently unavailable.
          </div>
        </div>

        <form className="chat-input">
          <input
            disabled
            placeholder="Direct messaging is not available yet"
          />
          <button className="primary-button" type="button" disabled>
            <Send size={17} />
          </button>
        </form>
      </section>
    </>
  );
}
