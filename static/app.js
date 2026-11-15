const authView = document.querySelector("#auth-view");
const appView = document.querySelector("#app-view");
const authForm = document.querySelector("#auth-form");
const authToggle = document.querySelector("#auth-toggle");
const authMessage = document.querySelector("#auth-message");
const authTitle = document.querySelector("#auth-title");
const authSubtitle = document.querySelector("#auth-subtitle");
const authEyebrow = document.querySelector("#auth-eyebrow");
const authSubmit = document.querySelector("#auth-submit");
const verificationForm = document.querySelector("#verification-form");
const verificationCopy = document.querySelector("#verification-copy");
const verificationToken = document.querySelector("#verification-token");
const verificationBack = document.querySelector("#verification-back");
const globalMessage = document.querySelector("#global-message");
let registerMode = false;
let overview = null;
let pendingVerificationEmail = "";
let latestGeneratedQuestions = [];
let questionOffset = 0;
const questionPageSize = 10;

const $ = (selector) => document.querySelector(selector);

function showMessage(element, message, error = false) {
  element.textContent = message || "";
  element.classList.toggle("error", error);
}

async function request(path, options = {}) {
  const response = await fetch(path, { credentials: "same-origin", ...options });
  let data = null;
  try { data = await response.json(); } catch (_) { /* empty response */ }
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : "Something went wrong.";
    throw new Error(detail);
  }
  return data;
}

function setAuthMode(isRegister) {
  registerMode = isRegister;
  authForm.hidden = false;
  verificationForm.hidden = true;
  authToggle.hidden = false;
  verificationBack.hidden = true;
  authEyebrow.textContent = registerMode ? "Start your preparation" : "Welcome back";
  authTitle.textContent = registerMode ? "Create your InterviewIQ account" : "Sign in to InterviewIQ";
  authSubtitle.textContent = registerMode ? "Save your documents, questions, and practice history." : "Your workspace is waiting for you.";
  authSubmit.textContent = registerMode ? "Create account" : "Sign in";
  authToggle.textContent = registerMode ? "Already registered? Sign in" : "Need an account? Register";
  $("#auth-password").autocomplete = registerMode ? "new-password" : "current-password";
  showMessage(authMessage, "");
}

function showVerificationStep(email, message) {
  pendingVerificationEmail = email;
  authForm.hidden = true;
  verificationForm.hidden = false;
  authToggle.hidden = true;
  verificationBack.hidden = false;
  authEyebrow.textContent = "Finish setting up";
  authTitle.textContent = "Verify your email";
  authSubtitle.textContent = "Confirm your address so your preparation workspace is ready when you return.";
  verificationCopy.textContent = `We sent a verification token to ${email}.`;
  showMessage(authMessage, message);
  verificationToken.value = "";
  verificationToken.focus();
}

function showSection(name) {
  document.querySelectorAll(".page-section").forEach((section) => {
    section.hidden = section.id !== `section-${name}`;
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.section === name);
    if (item.dataset.section === name) {
      item.setAttribute("aria-current", "page");
    } else {
      item.removeAttribute("aria-current");
    }
  });
  const titles = { overview: "Good to see you.", documents: "Build your context.", analysis: "Know your fit.", questions: "Practice with purpose.", interview: "Step into the room." };
  titles.assistant = "Get a personalized answer.";
  $("#page-title").textContent = titles[name] || titles.overview;
  if (name === "questions") loadQuestions();
  if (name === "interview") loadInterviews();
  if (name === "assistant") loadAssistantMessages();
}

function renderOverview() {
  const resume = overview.resume;
  const jd = overview.job_description;
  const analysis = overview.analysis;
  $("#user-email").textContent = overview.email;
  $("#resume-stat").textContent = resume ? `Version ${resume.version_no}` : "Not uploaded";
  $("#resume-stat-detail").textContent = resume?.file_name || "Add your latest version";
  $("#analysis-stat").textContent = analysis ? `Version ${analysis.analysis_version}` : "Not run";
  $("#analysis-stat-detail").textContent = analysis ? "Your latest role comparison" : "Compare your fit to a role";
  $("#question-stat").textContent = `${overview.question_count} question${overview.question_count === 1 ? "" : "s"}`;
  $("#interview-stat").textContent = `${overview.interview_count} completed`;
  $("#saved-resume").textContent = resume?.file_name || "None yet";
  $("#saved-resume-detail").textContent = resume ? `Resume version ${resume.version_no} is ready.` : "Upload a PDF to create your first resume version.";
  $("#saved-jd").textContent = jd ? `Job description v${jd.version_no}` : "None yet";
  $("#saved-jd-detail").textContent = jd ? "Your latest role context is saved." : "Paste a role description to begin.";
  $("#next-step-title").textContent = !resume || !jd ? "Upload your resume and target job description." : !analysis ? "Run your first role-fit analysis." : "Generate questions and practice aloud.";
  $("#next-step-copy").textContent = !resume || !jd ? "Start with your documents and InterviewIQ will build the rest of your preparation workspace." : !analysis ? "Your documents are ready. Analyze them to see strengths, gaps, and focused next steps." : "Your context is ready. Move from insight to deliberate practice.";
  const action = $("#next-step-action");
  action.textContent = (!resume || !jd) ? "Set up documents" : "Go to questions";
  action.dataset.go = (!resume || !jd) ? "documents" : "questions";
  if (analysis) {
    $("#analysis-empty").hidden = true;
    $("#analysis-content").hidden = false;
    $("#analysis-overview").textContent = analysis.overview || "No overview returned.";
    $("#analysis-match").textContent = analysis.match_analysis || "No match analysis returned.";
    $("#analysis-missing").textContent = analysis.missing_requirements || "No missing requirements returned.";
    $("#analysis-suggestions").textContent = analysis.suggestions || "No suggestions returned.";
  } else {
    $("#analysis-empty").hidden = false;
    $("#analysis-content").hidden = true;
  }
}

async function loadOverview() {
  overview = await request("/account/overview");
  authView.hidden = true;
  appView.hidden = false;
  renderOverview();
}

authToggle.addEventListener("click", () => setAuthMode(!registerMode));
authForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage(authMessage, "Working…");
  const payload = { email: $("#auth-email").value, password: $("#auth-password").value };
  try {
    if (registerMode) {
      const data = await request("/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      showVerificationStep(data.email, data.message);
    } else {
      await request("/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      await loadOverview();
      await loadQuestionOptions();
    }
  } catch (error) {
    showMessage(authMessage, error.message, true);
  }
});

verificationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage(authMessage, "Verifying…");
  try {
    await request("/account/verify-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: verificationToken.value.trim() }),
    });
    setAuthMode(false);
    $("#auth-email").value = pendingVerificationEmail;
    showMessage(authMessage, "Email verified. Sign in with your credentials.");
  } catch (error) {
    showMessage(authMessage, error.message, true);
  }
});

verificationBack.addEventListener("click", () => {
  setAuthMode(false);
  $("#auth-email").value = pendingVerificationEmail;
  showMessage(authMessage, "You can sign in with your valid credentials.");
});

document.querySelectorAll("[data-go]").forEach((button) => {
  button.addEventListener("click", () => showSection(button.dataset.go));
});
document.querySelectorAll(".nav-item").forEach((button) => {
  button.addEventListener("click", () => showSection(button.dataset.section));
});

$("#logout").addEventListener("click", async () => {
  try { await request("/logout", { method: "POST" }); } finally {
    appView.hidden = true;
    authView.hidden = false;
    showMessage(authMessage, "You have been logged out.");
  }
});

$("#resume-file").addEventListener("change", (event) => {
  $("#file-name").textContent = event.target.files[0]?.name || "PDF up to 5 MB";
});
$("#analyze-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData();
  form.append("resume", $("#resume-file").files[0]);
  form.append("job_description", $("#job-description").value);
  showMessage($("#upload-status"), "Uploading and analyzing…");
  try {
    await request("/analyze", { method: "POST", body: form });
    overview = await request("/account/overview");
    renderOverview();
    showMessage($("#upload-status"), "Analysis saved. Your workspace is updated.");
    showSection("analysis");
  } catch (error) {
    showMessage($("#upload-status"), error.message, true);
  }
});

async function loadQuestionOptions() {
  const options = await request("/questions/options");
  $("#question-count").value = options.count_default;
  $("#category-options").replaceChildren(...options.categories.map((category) => {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "categories";
    input.value = category.name;
    const text = document.createElement("span");
    text.textContent = category.label;
    label.append(input, text);
    return label;
  }));
  const filter = $("#question-category-filter");
  filter.replaceChildren(new Option("All categories", ""));
  options.categories.forEach((category) => {
    filter.append(new Option(category.label, category.name));
  });
}

function renderQuestionItems(items, total, title) {
  $("#question-bank-title").textContent = title;
  const list = $("#question-list");
  list.replaceChildren();
  items.forEach((question) => {
    const item = document.createElement("div");
    item.className = "question-item";
    const meta = document.createElement("small");
    meta.textContent = `${question.category.replace("_", " ")} · ${question.difficulty} · round ${question.batch_no}`;
    const text = document.createElement("p");
    text.textContent = question.question_text;
    item.append(meta, text);
    list.appendChild(item);
  });
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No questions match these filters.";
    list.appendChild(empty);
  }
  const first = total ? questionOffset + 1 : 0;
  const last = Math.min(questionOffset + items.length, total);
  $("#question-page-status").textContent = `Showing ${first}–${last} of ${total}`;
  $("#question-prev").disabled = questionOffset === 0;
  $("#question-next").disabled = last >= total;
}

function updateQuestionBatchOptions(items) {
  const filter = $("#question-batch-filter");
  const selected = filter.value;
  const batches = [...new Set(items.map((question) => question.batch_no))].sort((a, b) => b - a);
  filter.replaceChildren(new Option("All rounds", ""));
  batches.forEach((batch) => filter.append(new Option(`Round ${batch}`, String(batch))));
  filter.value = batches.includes(Number(selected)) ? selected : "";
}

async function loadQuestions() {
  try {
    const view = $("#question-view").value;
    if (view === "latest" && !$("#question-category-filter").value && !$("#question-batch-filter").value) {
      const data = await request(`/questions?limit=${questionPageSize}&offset=0`);
      questionOffset = 0;
      latestGeneratedQuestions = data.items;
      renderQuestionItems(data.items, data.total, `Latest generated · ${data.total} saved`);
      return;
    }

    const params = new URLSearchParams({
      limit: String(questionPageSize),
      offset: String(questionOffset),
    });
    const category = $("#question-category-filter").value;
    const batch = $("#question-batch-filter").value;
    if (category) params.set("category", category);
    if (batch) params.set("batch_no", batch);
    const data = await request(`/questions?${params}`);
    const allData = await request("/questions?limit=200");
    updateQuestionBatchOptions(allData.items);
    renderQuestionItems(data.items, data.total, `All saved · ${data.total} question${data.total === 1 ? "" : "s"}`);
  } catch (error) { showMessage(globalMessage, error.message, true); }
}

$("#questions-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const categories = [...document.querySelectorAll("#category-options input:checked")].map((input) => input.value);
  const payload = { count: Number($("#question-count").value), categories: categories.length ? categories : null, difficulty: $("#question-difficulty").value || null };
  showMessage($("#questions-status"), "Generating fresh questions…");
  try {
    const generated = await request("/questions/generate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    overview = await request("/account/overview");
    renderOverview();
    latestGeneratedQuestions = generated.questions || [];
    questionOffset = 0;
    $("#question-view").value = "latest";
    $("#question-category-filter").value = "";
    $("#question-batch-filter").value = "";
    renderQuestionItems(
      latestGeneratedQuestions,
      latestGeneratedQuestions.length,
      `${latestGeneratedQuestions.length} new question${latestGeneratedQuestions.length === 1 ? "" : "s"}`
    );
    showMessage($("#questions-status"), latestGeneratedQuestions.length
      ? "Only the newly created questions are shown. Use All saved questions to browse your history."
      : "No new questions were created; all generated questions were duplicates.");
  } catch (error) { showMessage($("#questions-status"), error.message, true); }
});
$("#refresh-questions").addEventListener("click", loadQuestions);
$("#question-view").addEventListener("change", () => {
  questionOffset = 0;
  loadQuestions();
});
$("#question-category-filter").addEventListener("change", () => {
  questionOffset = 0;
  $("#question-view").value = "all";
  loadQuestions();
});
$("#question-batch-filter").addEventListener("change", () => {
  questionOffset = 0;
  $("#question-view").value = "all";
  loadQuestions();
});
$("#question-prev").addEventListener("click", () => {
  questionOffset = Math.max(0, questionOffset - questionPageSize);
  loadQuestions();
});
$("#question-next").addEventListener("click", () => {
  questionOffset += questionPageSize;
  loadQuestions();
});

async function loadInterviews() {
  try {
    const data = await request("/interviews");
    const list = $("#interview-list");
    list.replaceChildren();
    data.items.slice(0, 8).forEach((interview) => {
      const item = document.createElement("button");
      item.className = "history-item";
      item.type = "button";
      const title = document.createElement("strong");
      title.textContent = `${interview.interview_type.replace("_", " ")} interview`;
      const meta = document.createElement("small");
      meta.textContent = `${interview.status} · ${interview.overall_score === null ? "Score pending" : `${interview.overall_score}/100`}`;
      item.append(title, meta);
      item.addEventListener("click", () => loadInterviewReview(interview.id));
      list.appendChild(item);
    });
    if (!data.items.length) list.innerHTML = '<p class="muted">No interviews yet.</p>';
  } catch (error) { showMessage(globalMessage, error.message, true); }
}
$("#refresh-interviews").addEventListener("click", loadInterviews);

function renderReviewList(selector, values, emptyText) {
  const list = $(selector);
  list.replaceChildren();
  const entries = Array.isArray(values) ? values.filter(Boolean) : [];
  if (!entries.length) {
    const empty = document.createElement("li");
    empty.textContent = emptyText;
    list.appendChild(empty);
    return;
  }
  entries.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    list.appendChild(item);
  });
}

function averageVoiceMetric(turns, key) {
  const values = turns.map((turn) => turn.voice?.[key]).filter((value) => Number.isFinite(value));
  return values.length ? Math.round(values.reduce((sum, value) => sum + value, 0) / values.length) : null;
}

async function loadInterviewReview(sessionId) {
  try {
    const data = await request(`/interviews/${sessionId}/review`);
    const summary = data.summary || {};
    $("#interview-review").hidden = false;
    $("#review-title").textContent = `${data.session.interview_type.replace("_", " ")} interview`;
    $("#review-summary").textContent = summary.summary_text || "This interview does not have a written summary yet.";
    const scoreGrid = $("#review-score-grid");
    scoreGrid.replaceChildren();
    [
      ["Overall", summary.overall_score],
      ["Fluency", averageVoiceMetric(data.turns, "fluency_score")],
      ["Clarity", averageVoiceMetric(data.turns, "clarity_score")],
      ["Confidence", averageVoiceMetric(data.turns, "confidence_score")],
      ["Pace", averageVoiceMetric(data.turns, "pace_score")],
      ["Pronunciation", averageVoiceMetric(data.turns, "pronunciation_score")],
    ].forEach(([label, value]) => {
      const card = document.createElement("div");
      card.className = "review-score";
      const name = document.createElement("small");
      name.textContent = label;
      const score = document.createElement("strong");
      score.textContent = value === null || value === undefined ? "—" : `${value}/100`;
      card.append(name, score);
      scoreGrid.appendChild(card);
    });
    renderReviewList("#review-strengths", summary.strong_areas, "No strengths recorded.");
    renderReviewList("#review-weaknesses", summary.weak_areas, "No improvement areas recorded.");
    renderReviewList("#review-recommendations", summary.recommendations, "No recommendations recorded.");
    const turns = $("#review-turns");
    turns.replaceChildren();
    data.turns.forEach((turn) => {
      const item = document.createElement("article");
      item.className = "review-turn";
      const heading = document.createElement("h4");
      heading.textContent = `Question ${turn.turn_no} · ${turn.question_category} · ${turn.difficulty}`;
      const question = document.createElement("p");
      question.className = "review-question";
      question.textContent = turn.question_text;
      const answer = document.createElement("p");
      answer.textContent = turn.user_transcript || "No transcript recorded.";
      const feedback = document.createElement("small");
      feedback.textContent = turn.answer_feedback || "No answer feedback recorded.";
      item.append(heading, question, answer, feedback);
      if (turn.voice) {
        const voice = document.createElement("div");
        voice.className = "review-voice";
        voice.textContent = `Voice: ${turn.voice.speaking_rate_wpm ?? "—"} WPM · ${turn.voice.pause_count ?? 0} pauses · ${turn.voice.filler_word_count ?? 0} filler words`;
        item.appendChild(voice);
      }
      turns.appendChild(item);
    });
    $("#interview-review").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) { showMessage(globalMessage, error.message, true); }
}

$("#close-interview-review").addEventListener("click", () => {
  $("#interview-review").hidden = true;
});

function renderAssistantMessages(messages) {
  const list = $("#assistant-messages");
  list.replaceChildren();
  if (!messages.length) {
    list.innerHTML = '<p class="muted">Ask me anything about your interview preparation.</p>';
    return;
  }
  messages.forEach((message) => {
    const item = document.createElement("article");
    item.className = `assistant-message ${message.role}`;
    const label = document.createElement("small");
    label.textContent = message.role === "user" ? "You" : "InterviewIQ Coach";
    const content = document.createElement("p");
    renderAssistantContent(content, message.content);
    item.append(label, content);
    list.appendChild(item);
  });
  list.lastElementChild?.scrollIntoView({ block: "nearest" });
}

function renderAssistantContent(container, source) {
  const lines = String(source || "").split(/\r?\n/);
  const linkPattern = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s<]+)/g;
  lines.forEach((line, lineIndex) => {
    let cursor = 0;
    const plainLine = line.replace(/\*\*/g, "");
    plainLine.replace(linkPattern, (match, markdownLabel, markdownUrl, plainUrl, offset) => {
      container.appendChild(document.createTextNode(plainLine.slice(cursor, offset)));
      const link = document.createElement("a");
      link.href = markdownUrl || plainUrl;
      link.textContent = markdownLabel || plainUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      container.appendChild(link);
      cursor = offset + match.length;
      return match;
    });
    container.appendChild(document.createTextNode(plainLine.slice(cursor)));
    if (lineIndex < lines.length - 1) container.appendChild(document.createElement("br"));
  });
}

async function loadAssistantMessages() {
  try {
    const data = await request("/assistant/messages");
    renderAssistantMessages(data.messages);
  } catch (error) {
    showMessage(globalMessage, error.message, true);
  }
}

$("#assistant-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = $("#assistant-input");
  const message = input.value.trim();
  if (!message) return;
  const button = event.currentTarget.querySelector("button[type='submit']");
  button.disabled = true;
  showMessage($("#assistant-status"), "Thinking…");
  try {
    await request("/assistant/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    input.value = "";
    await loadAssistantMessages();
    showMessage($("#assistant-status"), "");
  } catch (error) {
    showMessage($("#assistant-status"), error.message, true);
  } finally {
    button.disabled = false;
  }
});

$("#clear-assistant").addEventListener("click", async () => {
  if (!window.confirm("Clear your assistant conversation?")) return;
  try {
    await request("/assistant/messages", { method: "DELETE" });
    renderAssistantMessages([]);
    showMessage($("#assistant-status"), "Chat cleared.");
  } catch (error) {
    showMessage(globalMessage, error.message, true);
  }
});

Promise.all([loadOverview(), loadQuestionOptions()]).catch(() => {
  authView.hidden = false;
  appView.hidden = true;
});
