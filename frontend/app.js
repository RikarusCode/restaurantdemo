const API_URL = "http://localhost:8000/agent/run";

const examples = {
  availability: {
    restaurantName: "Kazu Sushi",
    restaurantPhone: "415-555-0142",
    userRequest: "Call this restaurant and ask if they have a table for 2 tonight at 7 PM.",
  },
  open: {
    restaurantName: "Luna Trattoria",
    restaurantPhone: "415-555-0188",
    userRequest: "Check if this restaurant is open right now.",
  },
  inferred: {
    restaurantName: "",
    restaurantPhone: "",
    userRequest: "Is Kazu Sushi open tomorrow at noon?",
  },
};

const form = document.querySelector("#agent-form");
const submitButton = document.querySelector("#submit-button");
const statusEl = document.querySelector("#status");
const restaurantNameEl = document.querySelector("#restaurant-name");
const restaurantPhoneEl = document.querySelector("#restaurant-phone");
const userRequestEl = document.querySelector("#user-request");
const resolvedInfoEl = document.querySelector("#resolved-info");
const parsedIntentEl = document.querySelector("#parsed-intent");
const toolInvocationEl = document.querySelector("#tool-invocation");
const toolResultEl = document.querySelector("#tool-result");
const finalSummaryEl = document.querySelector("#final-summary");

function pretty(value) {
  return JSON.stringify(value ?? null, null, 2);
}

function setLoading(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "Running..." : "Run agent";
  if (isLoading) {
    statusEl.textContent = "Checking with the agent...";
  }
}

function fillExample(exampleKey) {
  const example = examples[exampleKey];
  restaurantNameEl.value = example.restaurantName;
  restaurantPhoneEl.value = example.restaurantPhone;
  userRequestEl.value = example.userRequest;
}

function renderResponse(data) {
  const name = data.restaurant_name || "Not resolved";
  const phone = data.restaurant_phone || "Not resolved";
  resolvedInfoEl.textContent = `${name} · ${phone}`;
  parsedIntentEl.textContent = pretty(data.parsed_intent);
  toolInvocationEl.textContent = pretty(data.tool_invocation);
  toolResultEl.textContent = pretty(data.tool_result);
  finalSummaryEl.textContent = data.summary;

  if (data.parsed_intent?.clarification_needed || data.parsed_intent?.intent === "unsupported") {
    statusEl.textContent = "No tool call was needed for this response.";
  }
}

async function runAgent(event) {
  event.preventDefault();
  setLoading(true);

  const payload = {
    restaurant_name: restaurantNameEl.value.trim() || null,
    restaurant_phone: restaurantPhoneEl.value.trim() || null,
    user_request: userRequestEl.value.trim(),
  };

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    renderResponse(await response.json());
  } catch (error) {
    statusEl.textContent = "Could not reach the backend. Start FastAPI on http://localhost:8000.";
    finalSummaryEl.textContent = error.message;
  } finally {
    setLoading(false);
  }
}

document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => fillExample(button.dataset.example));
});

form.addEventListener("submit", runAgent);
