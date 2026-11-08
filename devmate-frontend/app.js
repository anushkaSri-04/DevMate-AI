
"use strict";

// ==================================================
// CONFIGURATION
// ==================================================

const API_BASE = "/api";

const state = {
  repository: null,
  sessionId: `devmate-${Date.now()}`,
  isSending: false
};

const $ = (id) => document.getElementById(id);

const welcomeTemplate = $("welcomeMessage")?.cloneNode(true);

// ==================================================
// API HELPER
// ==================================================

async function apiRequest(endpoint, data = null) {
  const options = {
    method: data ? "POST" : "GET",
    headers: {
      "Content-Type": "application/json"
    }
  };

  if (data !== null) {
    options.body = JSON.stringify(data);
  }

  let response;

  try {
    response = await fetch(`${API_BASE}${endpoint}`, options);
  } catch {
    throw new Error(
      "Cannot connect to DevMate API. Start the FastAPI backend on port 8000."
    );
  }

  const result = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      result.detail ||
      result.message ||
      `Request failed with status ${response.status}`
    );
  }

  return result;
}

function repositoryPayload() {
  if (!state.repository) {
    throw new Error("Please connect a repository first.");
  }

  return {
    owner: state.repository.owner,
    repo: state.repository.repo
  };
}

// ==================================================
// NOTIFICATIONS
// ==================================================

let toastTimer;

function showToast(message) {
  const toast = $("toast");

  if (!toast) return;

  toast.textContent = message;
  toast.classList.add("show");

  clearTimeout(toastTimer);

  toastTimer = setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

function setOperationStatus(message) {
  const note = $("previewNote");

  if (note) {
    note.textContent = message;
  }

  const hint = $("metricStatusHint");

  if (hint) {
    hint.textContent = message;
  }
}

function setButtonLoading(button, loading, normalText, loadingText) {
  button.disabled = loading;
  button.textContent = loading ? loadingText : normalText;
}

// ==================================================
// BACKEND HEALTH CHECK
// ==================================================

async function checkBackend() {
  const indicator = $("backendIndicator");

  if (!indicator) return;

  try {
    await apiRequest("/health");

    indicator.innerHTML = "<i></i> Backend connected";
    indicator.style.color = "#23805c";
    indicator.style.background = "#eaf8f1";

  } catch {
    indicator.innerHTML = "<i></i> Backend offline";
    indicator.style.color = "#c9434e";
    indicator.style.background = "#fdecee";
  }
}

// ==================================================
// NAVIGATION
// ==================================================

const pages = {
  overview: $("overviewView"),
  repository: $("repositoryView"),
  assistant: $("assistantView")
};

const pageTitles = {
  overview: "Overview",
  repository: "Repository",
  assistant: "Ask DevMate"
};

function navigate(pageName) {
  if (!pages[pageName]) return;

  Object.entries(pages).forEach(([name, element]) => {
    element?.classList.toggle("hidden", name !== pageName);
  });

  document.querySelectorAll(".nav-item[data-view]").forEach(button => {
    button.classList.toggle(
      "active",
      button.dataset.view === pageName
    );
  });

  $("breadcrumbPage").textContent = pageTitles[pageName];

  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
}

document.querySelectorAll(".nav-item[data-view]").forEach(button => {
  button.addEventListener("click", () => {
    navigate(button.dataset.view);
  });
});

$("brandLink")?.addEventListener("click", event => {
  event.preventDefault();
  navigate("overview");
});

// ==================================================
// CONNECT MODAL
// ==================================================

function openModal() {
  $("connectModal").classList.remove("hidden");
  $("formError").textContent = "";
  $("repoOwner").focus();
}

function closeModal() {
  $("connectModal").classList.add("hidden");
  $("formError").textContent = "";
}

[
  "openConnect",
  "bannerConnect",
  "repoConnect",
  "emptyConnect"
].forEach(id => {
  $(id)?.addEventListener("click", openModal);
});

$("closeModal").addEventListener("click", closeModal);

$("connectModal").addEventListener("click", event => {
  if (event.target === $("connectModal")) {
    closeModal();
  }
});

document.addEventListener("keydown", event => {
  if (
    event.key === "Escape" &&
    !$("connectModal").classList.contains("hidden")
  ) {
    closeModal();
  }
});

// ==================================================
// REPOSITORY UI
// ==================================================

function updateRepositoryUI(owner, repo) {
  state.repository = { owner, repo };

  $("sidebarRepo").textContent = repo;
  $("sidebarBranch").textContent = owner;

  $("sidebarStatus").classList.add("online");

  $("repoDetailEmpty").classList.add("hidden");
  $("repoDetail").classList.remove("hidden");

  $("detailRepoName").textContent = repo;
  $("detailRepoUrl").textContent =
    `github.com/${owner}/${repo}`;

  $("detailFiles").textContent = "—";
  $("detailChunks").textContent = "—";
  $("detailDeps").textContent = "—";

  $("metricFiles").textContent = "—";
  $("metricChunks").textContent = "—";
  $("metricDeps").textContent = "—";

  $("metricStatus").textContent = "Not indexed";
  $("metricStatusHint").textContent = "Repository connected";

  setOperationStatus("Repository connected. Ready for analysis.");
}

function disconnectRepository() {
  state.repository = null;

  $("sidebarRepo").textContent = "No repository";
  $("sidebarBranch").textContent = "Connect a GitHub repo";

  $("sidebarStatus").classList.remove("online");

  $("repoDetail").classList.add("hidden");
  $("repoDetailEmpty").classList.remove("hidden");

  $("metricFiles").textContent = "—";
  $("metricChunks").textContent = "—";
  $("metricDeps").textContent = "—";

  $("metricStatus").textContent = "Not indexed";
  $("metricStatusHint").textContent = "Connect a repository to begin";

  $("activityList").innerHTML = "";
  $("activityEmpty").classList.remove("hidden");

  clearChat(false);

  showToast("Repository disconnected.");
}

$("disconnectButton").addEventListener("click", disconnectRepository);

// ==================================================
// CONNECT REPOSITORY API
// ==================================================

async function connectRepository(owner, repo) {
  const button = $("connectSubmit");

  setButtonLoading(
    button,
    true,
    "Connect repository",
    "Connecting..."
  );

  $("formError").textContent = "";

  try {
    const result = await apiRequest(
      "/repository/connect",
      { owner, repo }
    );

    updateRepositoryUI(owner, repo);

    closeModal();
    $("connectForm").reset();

    navigate("repository");

    addActivity(
      "Repository connected",
      `${owner}/${repo}`
    );

    showToast(result.message || "Repository connected successfully.");

  } catch (error) {
    $("formError").textContent = error.message;

  } finally {
    setButtonLoading(
      button,
      false,
      "Connect repository",
      "Connecting..."
    );
  }
}

$("connectForm").addEventListener("submit", event => {
  event.preventDefault();

  const owner = $("repoOwner").value.trim();
  const repo = $("repoName").value.trim();

  if (!/^[A-Za-z0-9-]+$/.test(owner)) {
    $("formError").textContent = "Enter a valid GitHub owner.";
    return;
  }

  if (!/^[A-Za-z0-9._-]+$/.test(repo)) {
    $("formError").textContent = "Enter a valid repository name.";
    return;
  }

  connectRepository(owner, repo);
});

// ==================================================
// ACTIVITY
// ==================================================

function addActivity(title, description) {
  const list = $("activityList");

  $("activityEmpty").classList.add("hidden");

  const item = document.createElement("div");
  item.className = "activity-item";

  const icon = document.createElement("span");
  icon.className = "activity-symbol";
  icon.textContent = "✓";

  const content = document.createElement("div");

  const heading = document.createElement("strong");
  heading.textContent = title;

  const detail = document.createElement("small");
  detail.textContent = description;

  content.append(heading, detail);
  item.append(icon, content);

  list.prepend(item);
}

// ==================================================
// REPOSITORY ANALYSIS
// ==================================================

$("analyzeButton").addEventListener("click", async () => {
  const button = $("analyzeButton");

  try {
    const payload = repositoryPayload();

    setButtonLoading(
      button,
      true,
      "Analyze repository",
      "Analyzing..."
    );

    setOperationStatus(
      "Fetching repository and analyzing Python files..."
    );

    const result = await apiRequest(
      "/repository/analyze",
      payload
    );

    const summary = result.summary || {};

    const files = summary.total_files_analyzed ?? 0;

    const dependencies =
      summary.total_resolved_references ?? 0;

    $("metricFiles").textContent = files;
    $("metricDeps").textContent = dependencies;

    $("detailFiles").textContent = files;
    $("detailDeps").textContent = dependencies;

    $("metricStatus").textContent = "Analyzed";
    $("metricStatusHint").textContent =
      `${summary.total_python_files_found ?? files} Python files found`;

    setOperationStatus(
      `Analysis completed. ${files} Python files analyzed.`
    );

    addActivity(
      "Repository analysis completed",
      `${files} Python files analyzed`
    );

    showToast("Repository analysis completed.");

  } catch (error) {
    setOperationStatus(error.message);
    showToast(error.message);

  } finally {
    setButtonLoading(
      button,
      false,
      "Analyze repository",
      "Analyzing..."
    );
  }
});

// ==================================================
// REPOSITORY INDEXING
// ==================================================

$("indexButton").addEventListener("click", async () => {
  const button = $("indexButton");

  try {
    const payload = repositoryPayload();

    setButtonLoading(
      button,
      true,
      "Index code",
      "Indexing..."
    );

    setOperationStatus(
      "Creating code chunks and embeddings. This may take some time..."
    );

    const result = await apiRequest(
      "/repository/index",
      payload
    );

    const indexing = result.indexing || {};

    const chunks =
      indexing.chunks_stored ??
      indexing.total_chunks ??
      indexing.total_chunks_stored ??
      indexing.chunks ??
      indexing.total_chunks_created ??
      null;

    if (chunks !== null) {
      $("metricChunks").textContent = chunks;
      $("detailChunks").textContent = chunks;
    }

    $("metricStatus").textContent = "Indexed";
    $("metricStatusHint").textContent = "Code embeddings stored";

    setOperationStatus(
      `Repository indexing completed. ${chunks ?? "Code"} chunks processed.`
    );

    addActivity(
      "Repository indexing completed",
      `${chunks ?? "Code"} chunks indexed`
    );

    showToast("Repository indexed successfully.");

  } catch (error) {
    setOperationStatus(error.message);
    showToast(error.message);

  } finally {
    setButtonLoading(
      button,
      false,
      "Index code",
      "Indexing..."
    );
  }
});

// ==================================================
// CHAT MESSAGES
// ==================================================

function addMessage(text, sender) {
  const container = $("chatMessages");

  const row = document.createElement("div");
  row.className = `message-row ${sender}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = sender === "user" ? "D" : "✳";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  bubble.textContent = text;

  row.append(avatar, bubble);

  container.appendChild(row);
  container.scrollTop = container.scrollHeight;

  return bubble;
}

function addTypingIndicator() {
  const row = document.createElement("div");
  row.className = "message-row assistant";
  row.id = "typingIndicator";

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = "✳";

  const bubble = document.createElement("div");
  bubble.className = "message-bubble";

  const typing = document.createElement("span");
  typing.className = "typing";

  for (let i = 0; i < 3; i++) {
    typing.appendChild(document.createElement("i"));
  }

  bubble.appendChild(typing);
  row.append(avatar, bubble);

  $("chatMessages").appendChild(row);

  $("chatMessages").scrollTop =
    $("chatMessages").scrollHeight;
}

function clearChat(resetSession = true) {
  $("chatMessages").innerHTML = "";

  if (welcomeTemplate) {
    $("chatMessages").appendChild(
      welcomeTemplate.cloneNode(true)
    );
  }

  $("evidenceList").innerHTML = "";
  $("evidenceEmpty").classList.remove("hidden");

  if (resetSession) {
    state.sessionId = `devmate-${Date.now()}`;
  }
}

$("clearChat").addEventListener("click", () => {
  clearChat();
  showToast("Chat cleared.");
});

// ==================================================
// SOURCE EVIDENCE
// ==================================================

function displayEvidence(evidence) {
  const container = $("evidenceList");
  const emptyState = $("evidenceEmpty");

  container.innerHTML = "";

  if (!Array.isArray(evidence) || evidence.length === 0) {
    emptyState.classList.remove("hidden");
    return;
  }

  emptyState.classList.add("hidden");

  evidence.forEach(item => {
    const card = document.createElement("article");
    card.className = "evidence-card";

    const header = document.createElement("div");
    header.className = "evidence-card-head";

    const filename = document.createElement("strong");
    filename.textContent = item.file || "Unknown file";

    const lines = document.createElement("span");

    const start = item.start_line ?? "?";
    const end = item.end_line ?? "?";

    lines.textContent = `Lines ${start}–${end}`;

    header.append(filename, lines);

    const snippet = document.createElement("pre");
    snippet.textContent =
      item.snippet || "No source snippet available.";

    card.append(header, snippet);
    container.appendChild(card);
  });
}

// ==================================================
// ASK DEVMATE
// ==================================================

async function sendQuestion(question) {
  const cleanQuestion = question.trim();

  if (!cleanQuestion || state.isSending) return;

  if (!state.repository) {
    showToast("Connect a repository first.");
    openModal();
    return;
  }

  state.isSending = true;

  $("welcomeMessage")?.remove();

  addMessage(cleanQuestion, "user");

  const sendButton = $("sendButton");
  sendButton.disabled = true;

  addTypingIndicator();

  try {
    const result = await apiRequest(
      "/repository/ask",
      {
        ...repositoryPayload(),
        question: cleanQuestion,
        session_id: state.sessionId
      }
    );

    $("typingIndicator")?.remove();

    if (result.status === "error") {
      throw new Error(
        result.message || result.error || "Unable to answer question."
      );
    }

    addMessage(
      result.answer || "No answer was returned.",
      "assistant"
    );

    displayEvidence(result.evidence || []);

    addActivity(
      "Repository question answered",
      cleanQuestion
    );

  } catch (error) {
    $("typingIndicator")?.remove();

    addMessage(
      `Unable to answer: ${error.message}`,
      "error"
    );

    displayEvidence([]);

    showToast(error.message);

  } finally {
    state.isSending = false;
    sendButton.disabled = false;

    $("chatMessages").scrollTop =
      $("chatMessages").scrollHeight;
  }
}

// ==================================================
// CHAT FORM
// ==================================================

$("chatForm").addEventListener("submit", event => {
  event.preventDefault();

  const input = $("questionInput");
  const question = input.value.trim();

  if (!question) return;

  input.value = "";
  input.style.height = "auto";

  sendQuestion(question);
});

// Enter to send, Shift+Enter for a new line
$("questionInput").addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    $("chatForm").requestSubmit();
  }
});

// Auto-resize textarea
$("questionInput").addEventListener("input", event => {
  const input = event.target;

  input.style.height = "auto";
  input.style.height =
    `${Math.min(input.scrollHeight, 120)}px`;
});

// ==================================================
// SUGGESTED QUESTIONS
// ==================================================

document.addEventListener("click", event => {
  const button = event.target.closest("[data-question]");

  if (!button) return;

  navigate("assistant");

  sendQuestion(button.dataset.question);
});

// ==================================================
// INITIALIZATION
// ==================================================

function initializeApp() {
  navigate("overview");

  checkBackend();

  // Check backend availability periodically.
  setInterval(checkBackend, 30000);
}

initializeApp();
