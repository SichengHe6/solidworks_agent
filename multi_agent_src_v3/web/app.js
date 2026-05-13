const form = document.getElementById("chat-form");
const input = document.getElementById("message-input");
const log = document.getElementById("chat-log");
const button = document.getElementById("send-button");
const modelConfig = document.getElementById("model-config");

let sessionId = crypto.randomUUID();
const messageBodies = new Map();
let activeParallelPanel = null;

function maskBaseUrl(url) {
  return String(url || "").replace(/\/+$/, "");
}

function renderModelConfig(payload) {
  if (!modelConfig) return;
  const profiles = payload.profiles || {};
  const profileOrder = payload.profile_order || Object.keys(profiles);
  const profileLabels = payload.profile_labels || {};
  modelConfig.textContent = "";

  profileOrder.forEach((profile) => {
    const item = profiles[profile] || {};
    const label = item.label || profileLabels[profile] || profile;
    const card = document.createElement("div");
    card.className = "model-config-item";
    if (!item.api_key_configured) {
      card.classList.add("missing-key");
    }

    const title = document.createElement("div");
    title.className = "model-config-title";
    title.textContent = label;

    const model = document.createElement("div");
    model.className = "model-config-model";
    model.textContent = item.model || "未配置";

    const meta = document.createElement("div");
    meta.className = "model-config-meta";
    const keyState = item.api_key_configured
      ? `key: ${item.api_key_source || item.api_key_env || "已配置"}`
      : `${item.api_key_env || "API_KEY"} 未配置`;
    meta.textContent = `${item.provider || "unknown"} · ${maskBaseUrl(item.base_url)} · config.py · ${keyState}`;

    card.append(title, model, meta);
    modelConfig.appendChild(card);
  });
}

async function loadModelConfig() {
  if (!modelConfig) return;
  try {
    const response = await fetch("/api/model-config");
    if (!response.ok) throw new Error("模型配置读取失败");
    renderModelConfig(await response.json());
  } catch (error) {
    modelConfig.textContent = `模型配置读取失败：${error.message}`;
  }
}

function appendMessage(role, name, content) {
  const wrapper = document.createElement("article");
  wrapper.className = `message ${role}`;

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = name;

  const body = document.createElement("div");
  body.className = "message-body";
  body.textContent = content;

  wrapper.append(meta, body);
  log.appendChild(wrapper);
  scrollToBottom();
  return body;
}

function appendStatus(title, content) {
  return appendMessage("agent", title, content);
}

function scrollToBottom() {
  log.scrollTop = log.scrollHeight;
}

function setBusy(isBusy) {
  button.disabled = isBusy;
  input.disabled = isBusy;
}

function handleMessageStart(event) {
  const body = appendMessage("agent", event.agent_name || "Agent", "");
  if (event.message_id) {
    messageBodies.set(event.message_id, body);
  }
}

function handleDelta(event) {
  let body = event.message_id ? messageBodies.get(event.message_id) : null;
  if (!body) {
    body = appendMessage("agent", event.agent_name || "Agent", "");
    if (event.message_id) {
      messageBodies.set(event.message_id, body);
    }
  }
  body.textContent += event.content || "";
  scrollToBottom();
}

function handleMessageEnd(event) {
  if (event.message_id) {
    messageBodies.delete(event.message_id);
  }
}

function createParallelPanel(event) {
  const wrapper = document.createElement("article");
  wrapper.className = "message agent parallel-panel";

  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = "并行零件";

  const title = document.createElement("div");
  title.className = "parallel-title";
  title.textContent = `零件并行任务 0/${event.total || 0}`;

  const bar = document.createElement("div");
  bar.className = "parallel-bar";
  const fill = document.createElement("div");
  fill.className = "parallel-bar-fill";
  bar.appendChild(fill);

  const list = document.createElement("div");
  list.className = "parallel-list";

  activeParallelPanel = {
    total: event.total || 0,
    done: 0,
    title,
    fill,
    list,
    items: new Map(),
  };

  (event.part_ids || []).forEach((partId) => {
    const row = document.createElement("div");
    row.className = "parallel-row pending";
    row.textContent = `${partId || "part"} · waiting`;
    activeParallelPanel.items.set(partId, row);
    list.appendChild(row);
  });

  wrapper.append(meta, title, bar, list);
  log.appendChild(wrapper);
  scrollToBottom();
}

function handleParallelPartDone(event) {
  if (!activeParallelPanel) {
    createParallelPanel({ total: 0, part_ids: [] });
  }

  activeParallelPanel.done += 1;
  const total = activeParallelPanel.total || activeParallelPanel.done;
  activeParallelPanel.title.textContent = `零件并行任务 ${activeParallelPanel.done}/${total}`;
  activeParallelPanel.fill.style.width = `${Math.min(100, (activeParallelPanel.done / total) * 100)}%`;

  let row = activeParallelPanel.items.get(event.part_id);
  if (!row) {
    row = document.createElement("div");
    activeParallelPanel.list.appendChild(row);
    activeParallelPanel.items.set(event.part_id, row);
  }

  row.className = `parallel-row ${event.success ? "success" : "failed"}`;
  row.textContent = `${event.name || event.part_id} · ${event.success ? "完成" : "失败"}`;
  if (event.error) {
    row.textContent += ` · ${event.error}`;
  }
  scrollToBottom();
}

function handleParallelPartsEnd(event) {
  const results = event.results || [];
  const failed = results.filter((item) => !item.success);
  appendStatus(
    "并行零件",
    failed.length
      ? `并行零件阶段完成，失败 ${failed.length}/${results.length}：${failed.map((item) => item.part_id).join(", ")}`
      : `并行零件阶段完成，成功 ${results.length}/${results.length}`
  );
}

function handleState(event) {
  const context = event.context && Object.keys(event.context).length
    ? `\n${JSON.stringify(event.context, null, 2)}`
    : "";
  appendStatus("状态", `${event.state || ""}${context}`);
}

function handleToolResult(event) {
  const marker = event.success ? "成功" : "失败";
  appendStatus(`工具 · ${event.tool || "unknown"}`, `${marker}\n${event.content || ""}`);
}

function handleReviewResult(event) {
  const comments = event.comments_for_next_agent && event.comments_for_next_agent.length
    ? `\n\n下游建议:\n- ${event.comments_for_next_agent.join("\n- ")}`
    : "";
  appendStatus(
    `评审 · ${event.scope || "check"}`,
    `${event.severity || (event.pass ? "pass" : "failed")}\n${event.feedback || ""}${comments}`
  );
}

function handleEvent(event) {
  if (event.type === "message_start" && event.agent_name) {
    handleMessageStart(event);
  } else if (event.type === "delta") {
    handleDelta(event);
  } else if (event.type === "message_end") {
    handleMessageEnd(event);
  } else if (event.type === "status") {
    appendStatus("系统", event.message || "");
  } else if (event.type === "state") {
    handleState(event);
  } else if (event.type === "tool_result") {
    handleToolResult(event);
  } else if (event.type === "review_result") {
    handleReviewResult(event);
  } else if (event.type === "parallel_parts_start") {
    createParallelPanel(event);
  } else if (event.type === "parallel_part_done") {
    handleParallelPartDone(event);
  } else if (event.type === "parallel_parts_end") {
    handleParallelPartsEnd(event);
  } else if (event.type === "execution_log") {
    appendStatus(event.title || "执行日志", event.content || "");
  } else if (event.type === "error") {
    appendStatus("系统", `[Error] ${event.error || "Unknown error"}`);
  } else if (event.type === "done") {
    setBusy(false);
    input.focus();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  appendMessage("user", "用户", message);
  input.value = "";
  setBusy(true);

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-Id": sessionId,
      },
      body: JSON.stringify({ message }),
    });

    const returnedSessionId = response.headers.get("X-Session-Id");
    if (returnedSessionId) {
      sessionId = returnedSessionId;
    }

    if (!response.ok || !response.body) {
      const payload = await response.json().catch(() => ({ error: "请求失败" }));
      appendMessage("agent", "系统", payload.error || "请求失败");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        handleEvent(JSON.parse(line));
      }
    }
  } catch (error) {
    appendMessage("agent", "系统", `[Error] ${error.message}`);
  } finally {
    setBusy(false);
    input.focus();
  }
});

loadModelConfig();
