const API_BASE = window.location.origin;

const EXAMPLES = {
  natural: {
    restaurant: null,
    request: "check if the sushi place is avaliable at 6",
    search: true,
  },
  table: {
    restaurant: "Kazu Sushi",
    request: "Call this restaurant and ask if they have a table for 2 tonight at 7 PM.",
    search: false,
  },
  open: {
    restaurant: "Luna Trattoria",
    request: "Is this restaurant open right now?",
    search: false,
  },
  search: {
    restaurant: null,
    request: "Is Kazu Sushi open tomorrow at noon?",
    search: true,
  },
  clarify: {
    restaurant: "Harbor Garden",
    request: "Do they have room for 4?",
    search: false,
  },
};

const STEP_LABELS = {
  restaurant_info: "Restaurant",
  understanding: "Understood",
  tool_call: "Tool",
  tool_result: "Result",
  notice: "Notice",
  summary: "Answer",
};

let restaurants = [];
let traceVisible = true;

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
  submitButton.querySelector(".btn-label").textContent = enabled ? "Checking..." : "Check restaurant";
  submitButton.querySelector(".spinner").hidden = !enabled;
  runStatus.textContent = enabled ? "Running" : "Ready";
}

function resetRunState() {
  pipeline.innerHTML = "";
  finalAnswer.textContent = "Checking the restaurant...";
  answerContext.textContent = "The response will update as soon as the tool result is ready.";
}

function renderStep(step, index) {
  if (step.step === "summary") {
    finalAnswer.textContent = step.data.text;
    answerContext.textContent = "Completed with a mocked restaurant-call tool.";
  }

  const element = document.createElement("article");
  element.className = `trace-step trace-${step.step}`;
  element.style.animationDelay = `${Math.min(index * 35, 210)}ms`;

  const label = STEP_LABELS[step.step] || "Step";
  const number = step.step === "summary" ? "OK" : String(index + 1).padStart(2, "0");

  if (step.step === "restaurant_info") {
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
  finalAnswer.textContent = "I could not reach the local backend.";
  answerContext.textContent = message;
  pipeline.innerHTML = `
    <article class="trace-step trace-error">
      <div class="step-marker">!</div>
      <div class="step-content">
        <div class="step-label">Error</div>
        <h3>Backend unavailable</h3>
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
  pipeline.hidden = !traceVisible;
  traceToggle.textContent = traceVisible ? "Hide trace" : "Show trace";
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

loadRestaurants();
