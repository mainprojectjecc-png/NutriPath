import { useEffect, useState } from "react";
import {
  HeartPulse, Send, CheckCircle2, Clock, XCircle,
  Leaf, ThumbsDown, ThumbsUp, RefreshCw, ShieldCheck
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
  if (status === "Reviewed" || status === "Suggested") {
    return "suggested";
  }
  return status.toLowerCase();
}

function RequestStatusIcon({ status }) {
  if (status === "Accepted" || status === "Reviewed") {
    return <CheckCircle2 size={14} />;
  }
  if (status === "Rejected") {
    return <XCircle size={14} />;
  }
  return <Clock size={14} />;
}

function formatRequestDate(value) {
  if (!value) return "";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? ""
    : date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function activeRequestForMeal(requests, mealId) {
  if (!mealId) return null;
  return requests.find(request =>
    (request.Status === "Pending" || request.Status === "Reviewed") &&
    request.NutritionLogID != null &&
    String(request.NutritionLogID) === String(mealId)
  ) || null;
}

export default function HealthCoach({ user, setActivePage }) {
  const role = typeof user?.role === "string" ? user.role.trim().toLowerCase() : "";
  const isCoach = role === "coach";
  const isUser = Boolean(user) && !isCoach;

  const [requests, setRequests] = useState([]);
  const [meals, setMeals] = useState([]);
  const [foods, setFoods] = useState([]);
  const [selectedMealId, setSelectedMealId] = useState("");
  const [requestedFoodId, setRequestedFoodId] = useState("");
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
        const [nutrition, userRequests, activeFoods] = await Promise.all([
          getNutritionData(user.id),
          getFoodReplacementRequests(),
          getActiveFoods()
        ]);
        setMeals(nutrition.meals);
        setRequests(userRequests);
        setFoods(activeFoods);
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

    if (selectedMealRequest) {
      setMessage("A request for this logged meal is already active. Follow its status under Requests & recommendations.");
      return;
    }

    try {
      setSubmitting(true);
      await createFoodReplacementRequest(
        Number(selectedMealId),
        reason,
        requestedFoodId ? Number(requestedFoodId) : undefined
      );
      setMessage("Your request was sent to the coach.");
      setSelectedMealId("");
      setRequestedFoodId("");
      setReason("");
      await loadData();
    } catch (requestError) {
      const detail = requestError.response?.data?.detail || requestError.message || "Request failed.";
      if (requestError.status === 409) {
        setMessage(
          detail.toLowerCase().includes("active replacement request already exists")
            ? "A request for this logged meal is already active. Follow its status under Requests & recommendations."
            : "This request conflicts with the current data. Refresh your requests or choose another meal."
        );
        await loadData();
      } else {
        setError(detail);
      }
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
  const pendingRequests = requests.filter(request => request.Status === "Pending");
  const visibleRequests = isCoach ? pendingRequests : requests;
  const suggestionsCount = requests.filter(
    request => request.Suggestion?.Status === "Pending"
  ).length;
  const selectedMealRequest = activeRequestForMeal(requests, selectedMealId);

  function clearRequestFeedback() {
    setError("");
    setMessage("");
  }

  if (!user) {
    return <p className="form-message" role="alert">Sign in to open your Health Coach workspace.</p>;
  }

  return (
    <div className="health-coach-page">
      <div className="page-title-row">
        <div>
          <span className="eyebrow">
            {isCoach ? "NUTRIPATH · COACH WORKSPACE" : "NUTRIPATH · PERSONAL WELLNESS"}
          </span>
          <h1>{isCoach ? "Thoughtful care, made practical." : "Your health, with a little more guidance."}</h1>
          <p>
            {isCoach
              ? "Support every recommendation with care, context and a practical next step."
              : "Personal guidance to help make everyday food choices feel more achievable."}
          </p>
        </div>
        <span className="online-label">
          <span className="online-dot"></span>
          {isCoach ? "Coach workspace" : "Member workspace"}
        </span>
      </div>

      <section className="coach-banner">
        <div className="coach-icon">
          <HeartPulse size={31} strokeWidth={1.8} />
        </div>
        <div>
          <span className="coach-banner-kicker">SMALL STEPS. LASTING WELLNESS.</span>
          <h2>{isCoach ? "Good guidance starts with listening." : "A more considered way to eat well."}</h2>
          <p>
            {isCoach
              ? "Understand each member’s needs, then offer a thoughtful and realistic alternative."
              : "Share what works for you, explore alternatives and take the next step at your own pace."}
          </p>
        </div>
        <div className="coach-leaf" aria-hidden="true">✳</div>
      </section>

      {(message || error) && (
        <p className={`form-message coach-feedback${error ? " is-error" : " is-success"}`} role={error ? "alert" : "status"}>
          {error || message}
        </p>
      )}
      {loading && <p className="form-message coach-loading" role="status">Refreshing your latest information…</p>}

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="coach-section-label">{isCoach ? "MEMBER SUPPORT" : "PERSONALISE YOUR PLAN"}</span>
              <h3>{isCoach ? "Review a member request" : "Request a food alternative"}</h3>
              <p>
                {isCoach
                  ? "Explore the context, then recommend an option that feels realistic."
                  : "Tell your coach what you would like to change and why."}
              </p>
            </div>
            <span className="coach-heading-icon"><Leaf size={19} /></span>
          </div>

          {isCoach ? (
            <form className="request-form" onSubmit={handleSuggestion}>
              <label htmlFor="coach-request">Member request</label>
              <select
                id="coach-request"
                value={selectedRequestId}
                onChange={e => setSelectedRequestId(e.target.value)}
                required
              >
                <option value="">Choose a request to review</option>
                {pendingRequests.map(request => (
                  <option key={request.RequestID} value={request.RequestID}>
                    #{request.RequestID} · {requestFoodName(request)}
                  </option>
                ))}
              </select>

              <label htmlFor="suggested-food">Recommended alternative</label>
              <select
                id="suggested-food"
                value={suggestedFoodId}
                onChange={e => setSuggestedFoodId(e.target.value)}
                required
              >
                <option value="">Choose from the food catalogue</option>
                {foods.map(food => (
                  <option key={food.FoodID} value={food.FoodID}>
                    {food.FoodName}{food.Category ? ` · ${food.Category}` : ""}
                  </option>
                ))}
              </select>

              <label htmlFor="suggestion-message">A note for the member <span className="coach-optional">OPTIONAL</span></label>
              <textarea
                id="suggestion-message"
                value={suggestionMessage}
                onChange={e => setSuggestionMessage(e.target.value)}
                maxLength={1000}
                placeholder="For example: This option may suit the member’s preference while keeping the meal balanced."
              />
              <span className="coach-form-hint">
                {suggestionMessage.length} of 1,000 characters
              </span>

              <button
                className="primary-button"
                type="submit"
                disabled={submitting || pendingRequests.length === 0 || foods.length === 0}
              >
                <Send size={16} />
                {submitting ? "Sending recommendation…" : "Send recommendation"}
              </button>
              {foods.length === 0 && !loading && (
                <p className="form-message">The food catalogue is unavailable at the moment. Please try again shortly.</p>
              )}
            </form>
          ) : (
            <form className="request-form" onSubmit={handleRequest}>
              <label htmlFor="replacement-meal">Meal to update</label>
              <select
                id="replacement-meal"
                value={selectedMealId}
                onChange={e => {
                  setSelectedMealId(e.target.value);
                  clearRequestFeedback();
                }}
                required
              >
                <option value="">Choose a meal from your journal</option>
                {meals.map(meal => {
                  const activeRequest = activeRequestForMeal(requests, meal.id);
                  return (
                    <option key={meal.id} value={meal.id} disabled={Boolean(activeRequest)}>
                      {meal.foodName} - {meal.mealType} ({meal.date})
                      {activeRequest ? ` · Request ${requestStatus(activeRequest).toLowerCase()}` : ""}
                    </option>
                  );
                })}
              </select>
              {selectedMealRequest && (
                <p className="coach-request-notice" role="status">
                  There is already an active request for this meal. You can follow its progress in Requests & recommendations below.
                </p>
              )}

              <label htmlFor="replacement-reason">What would you like to change?</label>
              <select
                id="replacement-reason"
                value={reason}
                onChange={e => {
                  setReason(e.target.value);
                  clearRequestFeedback();
                }}
                required
              >
                <option value="">Choose what best describes it</option>
                <option>Personal preference</option>
                <option>Allergy or intolerance</option>
                <option>Not readily available</option>
                <option>Something else</option>
              </select>

              <label htmlFor="requested-food">An alternative you have in mind <span className="coach-optional">OPTIONAL</span></label>
              <select
                id="requested-food"
                value={requestedFoodId}
                onChange={e => {
                  setRequestedFoodId(e.target.value);
                  clearRequestFeedback();
                }}
                disabled={foods.length === 0}
              >
                <option value="">I’m open to a recommendation</option>
                {foods.map(food => (
                  <option key={food.FoodID} value={food.FoodID}>
                    {food.FoodName}{food.Category ? ` · ${food.Category}` : ""}
                  </option>
                ))}
              </select>
              <p className="coach-form-hint">
                Your coach will consider your preference and may recommend another suitable choice.
              </p>

              <button
                className="primary-button"
                type="submit"
                disabled={submitting || meals.length === 0 || Boolean(selectedMealRequest)}
              >
                <Send size={16} />
                {submitting ? "Sending your request…" : "Send request"}
              </button>

              {meals.length === 0 && !loading && (
                <div className="coach-next-step">
                  <div>
                    <strong>Start with a meal in your journal</strong>
                    <p>Once you’ve logged a meal, choose it here, tell your coach what you’d like to change, and send a request.</p>
                  </div>
                  <button className="small-button" type="button" onClick={() => setActivePage?.("Daily Meal Tracker")}>
                    Open meal tracker
                  </button>
                </div>
              )}
            </form>
          )}
        </section>

        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="coach-section-label">{isCoach ? "AT A GLANCE" : "YOUR PROGRESS"}</span>
              <h3>{isCoach ? "Request overview" : "Your request overview"}</h3>
              <p>
                {isCoach
                  ? "A clear view of member requests and recommendations."
                  : "Keep track of your requests and coach recommendations."}
              </p>
            </div>
            <span className="coach-heading-icon"><HeartPulse size={19} /></span>
          </div>

          <div className="request-stats">
            <div>
              <strong>{isCoach ? pendingCount : requests.length}</strong>
              <span>{isCoach ? "Pending" : "Total"}</span>
            </div>
            <div>
              <strong>{isCoach ? reviewedRequests.length : pendingCount}</strong>
              <span>{isCoach ? "Awaiting response" : "Awaiting review"}</span>
            </div>
            <div>
              <strong>{isCoach ? foods.length : suggestionsCount}</strong>
              <span>{isCoach ? "Foods to recommend" : "New suggestions"}</span>
            </div>
          </div>
        </section>
      </div>

      <section className="panel requests-panel">
        <div className="panel-heading">
          <div>
            <span className="coach-section-label">{isCoach ? "THE REQUEST QUEUE" : "YOUR WELLNESS JOURNEY"}</span>
            <h3>{isCoach ? "Member requests" : "Requests & recommendations"}</h3>
            <p>
              {isCoach
                ? "Each request is an opportunity to offer thoughtful, individual support."
                : "See what you’ve shared and review the guidance from your coach."}
            </p>
          </div>
          <button
            className="small-button"
            type="button"
            onClick={loadData}
            disabled={loading || submitting}
            aria-label="Refresh health coach requests"
          >
            <RefreshCw size={14} /> Refresh list
          </button>
        </div>

        {visibleRequests.length === 0 && !loading && (
          <div className="coach-empty-guide">
            <span className="coach-empty-guide-icon"><Leaf size={18} /></span>
            <div>
              <strong>{isCoach ? "Your request queue is ready" : "Your coaching journey starts here"}</strong>
              <p>{isCoach
                ? "Member requests will appear here after they log a meal and ask for an alternative. Review the reason, choose a suitable catalogue option, and add a thoughtful note."
                : "Log a meal, then request an alternative if a food does not suit your preferences, availability or needs. Your coach’s recommendation will appear here for you to review."}</p>
              {!isCoach && <button className="small-button" type="button" onClick={() => setActivePage?.("Daily Meal Tracker")}>Log a meal to begin</button>}
            </div>
          </div>
        )}

        {visibleRequests.map(request => {
          const status = requestStatus(request);
          const suggestedFood = request.Suggestion?.SuggestedFood?.FoodName;
          const canAccept = !isCoach && request.Suggestion?.Status === "Pending";

          return (
            <div className="request-row" key={request.RequestID}>
              <div className="request-food-icon" aria-hidden="true"><Leaf size={19} /></div>

              <div className="request-info">
                <strong>
                  {isCoach
                    ? `Request #${request.RequestID}: ${requestFoodName(request)}`
                    : requestFoodName(request)}
                </strong>
                {isCoach && request.RequestedFood?.FoodName && (
                  <span>Member’s preference: {request.RequestedFood.FoodName}</span>
                )}
                {isCoach && request.User?.FullName && (
                  <span>Requested by: {request.User.FullName}</span>
                )}
                {!isCoach && request.RequestedFood?.FoodName && (
                  <span>Preferred alternative: {request.RequestedFood.FoodName}</span>
                )}
                <span>Reason: {request.Reason || "Not specified"}</span>
                {formatRequestDate(request.CreatedAt) && (
                  <span>Requested {formatRequestDate(request.CreatedAt)}</span>
                )}
                {!isCoach && (
                  <span>
                    {suggestedFood ? `Coach recommendation: ${suggestedFood}` : "Your coach is reviewing this request"}
                    {request.Suggestion?.Message ? ` · ${request.Suggestion.Message}` : ""}
                  </span>
                )}
              </div>

              <div className="request-actions">
                <span className={`status ${statusClass(status)}`}>
                  <RequestStatusIcon status={status} />
                  {status}
                </span>

                {isCoach && (
                  <button
                    className="small-button"
                    type="button"
                    onClick={() => setSelectedRequestId(String(request.RequestID))}
                  >
                    Review request
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
                <span className="coach-section-label">WITH THE MEMBER</span>
                <h3>Recommendations shared</h3>
                <p>These members are considering their coach’s recommendation.</p>
              </div>
            </div>
            {reviewedRequests.map(request => (
              <div className="request-row" key={request.RequestID}>
                <div className="request-food-icon" aria-hidden="true"><Leaf size={19} /></div>
                <div className="request-info">
                  <strong>
                    Request #{request.RequestID}: {requestFoodName(request)}
                  </strong>
                  {request.User?.FullName && (
                    <span>Requested by: {request.User.FullName}</span>
                  )}
                  <span>Reason: {request.Reason || "Not specified"}</span>
                  {request.RequestedFood?.FoodName && (
                    <span>Member's preferred alternative: {request.RequestedFood.FoodName}</span>
                  )}
                  <span>
                    Suggested alternative: {request.Suggestion?.SuggestedFood?.FoodName || "Unavailable"}
                    {request.Suggestion?.Message ? ` · ${request.Suggestion.Message}` : ""}
                  </span>
                </div>
                <div className="request-actions">
                  <span className={`status ${statusClass(request.Status)}`}>
                    <RequestStatusIcon status={request.Status} />
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
                <span className="coach-section-label">CLOSED REQUESTS</span>
                <h3>Resolved requests</h3>
                <p>Recommendations accepted or declined by members.</p>
              </div>
            </div>
            {resolvedRequests.map(request => (
              <div className="request-row" key={request.RequestID}>
                <div className="request-food-icon" aria-hidden="true"><Leaf size={19} /></div>
                <div className="request-info">
                  <strong>
                    Request #{request.RequestID}: {requestFoodName(request)}
                  </strong>
                  {request.User?.FullName && (
                    <span>Requested by: {request.User.FullName}</span>
                  )}
                  <span>Reason: {request.Reason || "Not specified"}</span>
                  {request.RequestedFood?.FoodName && (
                    <span>Member’s preferred alternative: {request.RequestedFood.FoodName}</span>
                  )}
                  <span>
                    Suggested alternative: {request.Suggestion?.SuggestedFood?.FoodName || "Unavailable"}
                    {request.Suggestion?.Message ? ` · ${request.Suggestion.Message}` : ""}
                  </span>
                </div>
                <div className="request-actions">
                  <span className={`status ${statusClass(request.Status)}`}>
                    <RequestStatusIcon status={request.Status} />
                    {request.Status}
                  </span>
                </div>
              </div>
            ))}
          </>
        )}
      </section>

      <section className="panel coach-guidance-panel">
        <div className="panel-heading">
          <div>
            <span className="coach-section-label">A BETTER WAY FORWARD</span>
            <h3><ShieldCheck size={19} /> {isCoach ? "Care that puts people first" : "Make every recommendation your own"}</h3>
            <p>Practical, considered support—always shaped around the person.</p>
          </div>
        </div>

        <div className="coach-guidance-grid">
          <article>
            <strong>{isCoach ? "Listen to the context" : "Start with what matters"}</strong>
            <p>
              {isCoach
                ? "Consider each member’s preferences and circumstances before recommending a change."
                : "Tell your coach about the preference, availability concern or intolerance behind your request."}
            </p>
          </article>
          <article>
            <strong>{isCoach ? "Recommend with purpose" : "Choose what feels right"}</strong>
            <p>
              {isCoach
                ? "Offer an achievable option from the catalogue, with a clear and supportive note."
                : "Consider how the recommendation fits your needs. You can accept it or decline it."}
            </p>
          </article>
          <article>
            <strong>Keep wellbeing in focus</strong>
            <p>
              Food suggestions are general guidance, not medical advice. For allergies or specific health concerns,
              speak with a qualified health professional.
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}
