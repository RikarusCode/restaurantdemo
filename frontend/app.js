const API_BASE = window.location.origin;

const EXAMPLES = {
  natural: {
    restaurant: null,
    request: "Can you check whether the sushi place has a table for 2 tonight at 6?",
    search: true,
  },
  table: {
    restaurant: "Kazu Sushi",
    request: "Can you ask this restaurant about a table for 2 tonight at 7 PM?",
    search: false,
  },
  open: {
    restaurant: "Luna Trattoria",
    request: "Can you check whether this restaurant is open right now?",
    search: false,
  },
  tacos: {
    restaurant: null,
    request: "Can you check whether the taco place has room for 6 around 6?",
    search: true,
  },
  search: {
    restaurant: null,
    request: "Can you check whether Kazu Sushi is open tomorrow at noon?",
    search: true,
  },
  clarify: {
    restaurant: "Harbor Garden",
    request: "Can you check whether this restaurant has room for 4?",
    search: false,
  },
  reservation: {
    restaurant: null,
    request: "Make a reservation for 2 tonight at 6 at the sushi place.",
    search: true,
  },
  unsupported: {
    restaurant: "Kazu Sushi",
    request: "Can you order delivery from this restaurant?",
    search: false,
  },
};

const STEP_LABELS = {
  llm_planning: "LLM",
  llm_decision: "LLM",
  agent_loop: "Loop",
  local_parser: "Fallback",
  restaurant_info: "Restaurant",
  understanding: "Understood",
  tool_call: "Tool",
  tool_result: "Result",
  notice: "Notice",
  summary: "Answer",
};

let restaurants = [];
let traceVisible = false;

const restaurantSelect = document.getElementById("restaurant-select");
const restaurantDetails = document.getElementById("restaurant-details");
const restaurantTable = document.getElementById("restaurant-table");
const searchMode = document.getElementById("search-mode");
const form = document.getElementById("agent-form");
const textarea = document.getElementById("user-request");
const submitButton = document.getElementById("submit-btn");
const pipeline = document.getElementById("pipeline");
const runStatus = document.getElementById("run-status");
const finalAnswer = document.getElementById("final-answer");
const answerContext = document.getElementById("answer-context");
const traceToggle = document.getElementById("trace-toggle");
const reservationActions = document.getElementById("reservation-actions");
const reservationModal = document.getElementById("reservation-modal");
const reservationForm = document.getElementById("reservation-form");

async function loadRestaurants() {
  try {
    const response = await fetch(`${API_BASE}/api/restaurants`);
    restaurants = await response.json();
  } catch {
    restaurants = [];
  }

  renderRestaurantOptions();
  renderRestaurantTable();
}

function renderRestaurantOptions() {
  restaurantSelect.innerHTML = "";

  restaurants.forEach((restaurant, index) => {
    const option = document.createElement("option");
    option.value = index;
    option.textContent = restaurant.name;
    restaurantSelect.appendChild(option);
  });

  renderRestaurantDetails();
}

function renderRestaurantDetails() {
  const restaurant = restaurants[restaurantSelect.value];
  if (!restaurant) {
    restaurantDetails.innerHTML = "<p>No restaurants loaded.</p>";
    return;
  }

  restaurantDetails.innerHTML = `
    <div>
      <strong>${escapeHtml(restaurant.name)}</strong>
      <span>${escapeHtml(restaurant.cuisine)} &middot; ${escapeHtml(restaurant.neighborhood)}</span>
    </div>
    <p>${escapeHtml(restaurant.phone)} &middot; ${escapeHtml(restaurant.address)}</p>
    <p>${escapeHtml(restaurant.summary)}</p>
  `;
}

function renderRestaurantTable() {
  const today = new Date().toLocaleDateString(undefined, { weekday: "long" });
  restaurantTable.innerHTML = restaurants.map((restaurant) => {
    const hours = restaurant.hours?.[today] || ["Closed", ""];
    const tonight = Object.entries(restaurant.availability?.tonight || {})
      .map(([time, slot]) => `${time}: ${slot.available ? `up to ${slot.max_party_size}` : "booked"}`)
      .slice(0, 4)
      .join(", ");

    return `
      <tr>
        <td>
          <strong>${escapeHtml(restaurant.name)}</strong>
          <span>${escapeHtml(restaurant.phone)}</span>
        </td>
        <td>${escapeHtml(restaurant.style)}<span>${escapeHtml(restaurant.price_range)}</span></td>
        <td>${escapeHtml(hours[0])} to ${escapeHtml(hours[1])}</td>
        <td>${escapeHtml(restaurant.aliases.slice(0, 4).join(", "))}</td>
        <td>${escapeHtml(tonight)}</td>
      </tr>
    `;
  }).join("");
}

function setSearchMode(enabled) {
  searchMode.checked = enabled;
  restaurantSelect.disabled = enabled;
  restaurantDetails.classList.toggle("muted", enabled);
}

function setLoading(enabled) {
  submitButton.disabled = enabled;
  submitButton.querySelector(".btn-label").textContent = enabled ? "Checking..." : "Run check";
  submitButton.querySelector(".spinner").hidden = !enabled;
  runStatus.textContent = enabled ? "Running" : "Ready";
}

function resetRunState() {
  pipeline.innerHTML = "";
  finalAnswer.textContent = "Checking...";
  answerContext.textContent = "The agent is planning the request and selecting the next tool.";
  clearReservationCta();
}

function clearReservationCta() {
  reservationActions.hidden = true;
  reservationActions.innerHTML = "";
}

function syncReservationCta(ui) {
  const button = ui?.reservation_button;
  const modal = ui?.reservation_modal;

  if (!button?.visible) {
    reservationActions.hidden = true;
    reservationActions.innerHTML = "";
    return;
  }

  reservationActions.hidden = false;
  reservationActions.innerHTML = `
    <button type="button" class="cta-btn" id="reservation-open" ${button.enabled ? "" : "disabled"}>
      ${escapeHtml(button.label)}
    </button>
    ${button.disabled_reason ? `<p class="reservation-note">${escapeHtml(button.disabled_reason)}</p>` : ""}
  `;

  if (button.enabled) {
    document.getElementById("reservation-open").addEventListener("click", () => openReservationModal(modal));
  }

  if (button.enabled && modal?.auto_open) {
    queueMicrotask(() => openReservationModal(modal));
  }
}

function openReservationModal(block) {
  const draft = block?.draft;
  if (!draft) return;

  document.getElementById("rf-restaurant").value = draft.restaurant_name || "";
  document.getElementById("rf-location").value = draft.location || "";
  document.getElementById("rf-guest").value = draft.guest_name || "";
  document.getElementById("rf-date").value = draft.date_heading || "";
  document.getElementById("rf-time").value = draft.time || "";
  document.getElementById("rf-party").value = draft.party_size ?? 2;
  document.getElementById("rf-phone").value = draft.restaurant_phone || "";
  document.getElementById("rf-date-token").value = draft.requested_date || "";
  document.getElementById("rf-notes").value = "";
  reservationModal.hidden = false;
}

function closeReservationModal() {
  reservationModal.hidden = true;
}

function syncTraceVisibility() {
  pipeline.hidden = !traceVisible;
  traceToggle.textContent = traceVisible ? "Hide trace" : "Show trace";
  traceToggle.setAttribute("aria-expanded", String(traceVisible));
}

function renderStep(step, index) {
  if (step.step === "summary") {
    finalAnswer.textContent = step.data.text;
    answerContext.textContent = "Resolved through the agent planner and restaurant tool.";
    syncReservationCta(step.data.ui);
  }

  const element = document.createElement("article");
  element.className = `trace-step trace-${step.step}`;
  element.style.animationDelay = `${Math.min(index * 35, 210)}ms`;

  const label = STEP_LABELS[step.step] || "Step";
  const number = step.step === "summary" ? "OK" : String(index + 1).padStart(2, "0");

  if (step.step === "llm_planning" || step.step === "llm_decision" || step.step === "agent_loop") {
    element.innerHTML = `
      <div class="step-marker">${number}</div>
      <div class="step-content agent-step">
        <div class="step-label">${escapeHtml(label)}</div>
        <h3>${escapeHtml(step.title)}</h3>
        ${renderKeyValueList(step.data)}
      </div>
    `;
  } else if (step.step === "restaurant_info") {
    element.innerHTML = `
      <div class="step-marker">${number}</div>
      <div class="step-content">
        <div class="step-label">${escapeHtml(label)}</div>
        <h3>${escapeHtml(step.title)}</h3>
        <p><strong>${escapeHtml(step.data.name)}</strong> &middot; ${escapeHtml(step.data.phone)}</p>
        ${step.data.cuisine ? `<p class="meta">${escapeHtml(step.data.cuisine)} &middot; ${escapeHtml(step.data.address)}</p>` : ""}
      </div>
    `;
  } else if (step.step === "understanding") {
    element.innerHTML = `
      <div class="step-marker">${number}</div>
      <div class="step-content compact-step">
        <div class="step-label">${escapeHtml(label)}</div>
        ${renderUnderstanding(step.data)}
      </div>
    `;
  } else if (step.step === "summary") {
    element.innerHTML = `
      <div class="step-marker">${number}</div>
      <div class="step-content compact-step">
        <div class="step-label">${escapeHtml(label)}</div>
        <p>${escapeHtml(step.data.text)}</p>
      </div>
    `;
  } else {
    element.innerHTML = `
      <div class="step-marker">${number}</div>
      <div class="step-content">
        <div class="step-label">${escapeHtml(label)}</div>
        <h3>${escapeHtml(step.title)}</h3>
        <pre>${prettyJson(step.data)}</pre>
      </div>
    `;
  }

  pipeline.appendChild(element);
}

function renderKeyValueList(data) {
  return `
    <dl class="kv-list">
      ${Object.entries(data).map(([key, value]) => `
        <div>
          <dt>${escapeHtml(key.replaceAll("_", " "))}</dt>
          <dd>${escapeHtml(formatValue(value))}</dd>
        </div>
      `).join("")}
    </dl>
  `;
}

function renderUnderstanding(data) {
  const chips = Object.entries(data)
    .filter(([key, value]) => key !== "assumptions" && value !== null && value !== undefined)
    .map(([key, value]) => `<span class="chip">${escapeHtml(key)}: ${escapeHtml(value)}</span>`)
    .join("");

  const assumptions = Object.values(data.assumptions || {}).filter(Boolean);
  const assumptionText = assumptions.length
    ? `<p class="assumption">${escapeHtml(assumptions.join(" "))}</p>`
    : "";

  return `<div class="chip-row">${chips}</div>${assumptionText}`;
}

function renderError(message) {
  clearReservationCta();
  finalAnswer.textContent = "The local service is unavailable.";
  answerContext.textContent = message;
  pipeline.innerHTML = `
    <article class="trace-step trace-error">
      <div class="step-marker">!</div>
      <div class="step-content">
        <div class="step-label">Error</div>
        <h3>Service unavailable</h3>
        <p>${escapeHtml(message)}</p>
      </div>
    </article>
  `;
  runStatus.textContent = "Error";
}

async function runAgent(event) {
  event.preventDefault();
  resetRunState();
  setLoading(true);

  const payload = { user_request: textarea.value.trim() };
  if (!searchMode.checked) {
    const restaurant = restaurants[restaurantSelect.value];
    if (restaurant) {
      payload.restaurant_name = restaurant.name;
      payload.restaurant_phone = restaurant.phone;
    }
  }

  try {
    const response = await fetch(`${API_BASE}/agent/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}.`);
    }

    await readNdjson(response, renderStep);
  } catch (error) {
    renderError(error.message);
  } finally {
    setLoading(false);
  }
}

async function readNdjson(response, onStep) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let index = 0;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop();

    for (const line of lines) {
      if (!line.trim()) continue;
      onStep(JSON.parse(line), index);
      index += 1;
    }
  }

  if (buffer.trim()) {
    onStep(JSON.parse(buffer), index);
  }
}

function prettyJson(value) {
  return escapeHtml(JSON.stringify(value, null, 2));
}

function formatValue(value) {
  if (Array.isArray(value)) return value.join(", ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return value ?? "";
}

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = value ?? "";
  return element.innerHTML;
}

restaurantSelect.addEventListener("change", renderRestaurantDetails);
searchMode.addEventListener("change", () => setSearchMode(searchMode.checked));
form.addEventListener("submit", runAgent);
traceToggle.addEventListener("click", () => {
  traceVisible = !traceVisible;
  syncTraceVisibility();
});

document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => {
    const example = EXAMPLES[button.dataset.example];
    setSearchMode(example.search);
    textarea.value = example.request;

    if (example.restaurant) {
      const index = restaurants.findIndex((restaurant) => restaurant.name === example.restaurant);
      if (index >= 0) {
        restaurantSelect.value = index;
        renderRestaurantDetails();
      }
    }

    form.requestSubmit();
  });
});

reservationModal.querySelectorAll("[data-close-modal]").forEach((el) => {
  el.addEventListener("click", closeReservationModal);
});

reservationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitBtn = document.getElementById("rf-submit");
  const label = submitBtn.querySelector(".btn-label");
  const spinner = submitBtn.querySelector(".spinner");

  label.textContent = "Calling...";
  submitBtn.disabled = true;
  spinner.hidden = false;

  const payload = {
    restaurant_name: document.getElementById("rf-restaurant").value.trim(),
    restaurant_phone: document.getElementById("rf-phone").value.trim(),
    location: document.getElementById("rf-location").value.trim() || null,
    guest_name: document.getElementById("rf-guest").value.trim() || null,
    party_size: Number(document.getElementById("rf-party").value),
    requested_time: document.getElementById("rf-time").value.trim(),
    date_heading: document.getElementById("rf-date").value.trim(),
    requested_date_token: document.getElementById("rf-date-token").value.trim() || null,
    notes: document.getElementById("rf-notes").value.trim() || null,
  };

  try {
    finalAnswer.textContent = "Calling the restaurant...";
    answerContext.textContent = "The Retell agent is placing the outbound reservation call.";

    const response = await fetch(`${API_BASE}/reservation/call`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}.`);
    }

    const data = await response.json();
    if (data.confirmed) {
      finalAnswer.textContent = "Your reservation is confirmed.";
      answerContext.textContent = callOutcomeText(data);
      closeReservationModal();
      clearReservationCta();
    } else {
      finalAnswer.textContent = "We could not confirm a reservation on this call.";
      answerContext.textContent = callOutcomeText(data);
      closeReservationModal();
    }
  } catch (error) {
    finalAnswer.textContent = "We could not complete the reservation call.";
    answerContext.textContent = error.message;
    closeReservationModal();
  } finally {
    label.textContent = "Attempt reservation";
    submitBtn.disabled = false;
    spinner.hidden = true;
  }
});

function callOutcomeText(data) {
  if (data.confirmed) {
    return data.message || "The restaurant confirmed the reservation.";
  }

  if (data.call_state === "not_configured" || data.call_state === "start_failed") {
    return "The reservation call could not be started. Check the calling setup, then try again.";
  }

  if (data.call_state === "timed_out") {
    return "The call took too long to finish. Check Retell for the final call result.";
  }

  if (data.call_state === "poll_failed") {
    return "The call started, but the final result did not come back. Check the call dashboard for details.";
  }

  return data.message || "No reservation was confirmed.";
}

loadRestaurants();
syncTraceVisibility();
