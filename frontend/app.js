(() => {
  "use strict";

  const state = {
    menu: null,
    attributes: {},
    passwordStatus: {},
    pendingReboot: null,
    activeTab: null,
    activeSubsection: null,
    stagedChanges: new Map(), // name -> value
  };

  const el = {
    tabs: document.getElementById("tabs"),
    subsections: document.getElementById("subsections"),
    settings: document.getElementById("settings"),
    pendingIndicator: document.getElementById("pending-indicator"),
    btnDiscard: document.getElementById("btn-discard"),
    btnRebootOnly: document.getElementById("btn-reboot-only"),
    btnSave: document.getElementById("btn-save"),
    modalBackdrop: document.getElementById("modal-backdrop"),
    modalTitle: document.getElementById("modal-title"),
    modalBody: document.getElementById("modal-body"),
    modalActions: document.getElementById("modal-actions"),
  };

  async function api(path, options) {
    const res = await fetch(path, options);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `${res.status} ${res.statusText}`);
    }
    return res.json();
  }

  function showModal(title, bodyHtml, actions) {
    el.modalTitle.textContent = title;
    el.modalBody.innerHTML = bodyHtml;
    el.modalActions.innerHTML = "";
    for (const action of actions) {
      const btn = document.createElement("button");
      btn.className = "key-btn" + (action.primary ? " primary" : "");
      btn.textContent = action.label;
      btn.onclick = action.onClick;
      el.modalActions.appendChild(btn);
    }
    el.modalBackdrop.hidden = false;
  }

  function hideModal() {
    el.modalBackdrop.hidden = true;
  }

  async function loadAll() {
    const [menu, attrsResp] = await Promise.all([
      api("/api/menu"),
      api("/api/attributes"),
    ]);
    state.menu = menu;
    state.attributes = attrsResp.attributes;
    state.passwordStatus = attrsResp.password_status;
    state.pendingReboot = attrsResp.pending_reboot;

    const tabNames = Object.keys(menu.sections);
    state.activeTab = tabNames[0];
    state.activeSubsection = menu.sections[state.activeTab][0][0];

    renderTabs();
    renderSubsections();
    renderSettings();
    renderPendingBanner();
  }

  function renderTabs() {
    el.tabs.innerHTML = "";
    for (const tabName of Object.keys(state.menu.sections)) {
      const div = document.createElement("div");
      div.className = "tab" + (tabName === state.activeTab ? " active" : "");
      div.textContent = tabName;
      div.onclick = () => {
        state.activeTab = tabName;
        state.activeSubsection = state.menu.sections[tabName][0][0];
        renderTabs();
        renderSubsections();
        renderSettings();
      };
      el.tabs.appendChild(div);
    }
  }

  function renderSubsections() {
    el.subsections.innerHTML = "";
    const subs = state.menu.sections[state.activeTab];
    for (const [title] of subs) {
      const div = document.createElement("div");
      div.className = "subsection-item" + (title === state.activeSubsection ? " active" : "");
      div.textContent = title;
      div.onclick = () => {
        state.activeSubsection = title;
        renderSubsections();
        renderSettings();
      };
      el.subsections.appendChild(div);
    }
  }

  function currentValueFor(name) {
    if (state.stagedChanges.has(name)) return state.stagedChanges.get(name);
    const attr = state.attributes[name];
    return attr ? attr.current_value : "";
  }

  function stageChange(name, value) {
    const attr = state.attributes[name];
    if (attr && attr.current_value === value) {
      state.stagedChanges.delete(name);
    } else {
      state.stagedChanges.set(name, value);
    }
    renderSettings();
  }

  function renderSettings() {
    el.settings.innerHTML = "";
    const subs = state.menu.sections[state.activeTab];
    const entry = subs.find(([title]) => title === state.activeSubsection);
    if (!entry) return;
    const [, names] = entry;

    for (const name of names) {
      const attr = state.attributes[name];
      const row = document.createElement("div");
      row.className = "setting-row";

      const isAction = state.menu.action_attributes.includes(name);
      const isReadOnly = state.menu.read_only_hints.includes(name);
      const isStaged = state.stagedChanges.has(name);
      if (isStaged) row.classList.add("changed");
      if (isReadOnly) row.classList.add("readonly");

      const label = document.createElement("div");
      label.className = "setting-label";
      label.textContent = attr ? name : name;
      if (!attr) {
        const badge = document.createElement("span");
        badge.className = "unknown-badge";
        badge.textContent = "not found on this system";
        label.appendChild(badge);
      }
      row.appendChild(label);

      const control = document.createElement("div");
      control.className = "setting-control";

      if (!attr) {
        control.innerHTML = '<span class="readonly-value">&mdash;</span>';
      } else if (isAction) {
        const btn = document.createElement("button");
        btn.className = "action-button";
        btn.textContent = "Run";
        btn.onclick = () => stageChange(name, attr.possible_values[0] || "1");
        control.appendChild(btn);
      } else if (isReadOnly) {
        const span = document.createElement("span");
        span.className = "readonly-value";
        span.textContent = attr.current_value || "—";
        control.appendChild(span);
      } else if (attr.widget === "toggle") {
        const wrap = document.createElement("div");
        wrap.className = "toggle";
        for (const val of attr.possible_values) {
          const btn = document.createElement("button");
          btn.textContent = val;
          btn.className = currentValueFor(name) === val ? "on" : "";
          btn.onclick = () => stageChange(name, val);
          wrap.appendChild(btn);
        }
        control.appendChild(wrap);
      } else if (attr.widget === "select") {
        const select = document.createElement("select");
        for (const val of attr.possible_values) {
          const opt = document.createElement("option");
          opt.value = val;
          opt.textContent = val;
          opt.selected = currentValueFor(name) === val;
          select.appendChild(opt);
        }
        select.onchange = () => stageChange(name, select.value);
        control.appendChild(select);
      } else if (attr.widget === "number") {
        const input = document.createElement("input");
        input.type = "number";
        input.value = currentValueFor(name);
        input.onchange = () => stageChange(name, input.value);
        control.appendChild(input);
      } else {
        const input = document.createElement("input");
        input.type = "text";
        input.value = currentValueFor(name);
        input.onchange = () => stageChange(name, input.value);
        control.appendChild(input);
      }

      row.appendChild(control);
      el.settings.appendChild(row);
    }

    if (names.length === 0) {
      el.settings.innerHTML = '<div class="loading">No settings in this section.</div>';
    }
  }

  function renderPendingBanner() {
    el.pendingIndicator.hidden = !state.pendingReboot;
  }

  el.btnDiscard.onclick = () => {
    if (state.stagedChanges.size === 0) return;
    state.stagedChanges.clear();
    renderSettings();
  };

  el.btnRebootOnly.onclick = () => {
    showModal(
      "Reboot the NAS?",
      "This performs a graceful <code>systemctl reboot</code> (not a hard power cycle). " +
        "The NAS and any running apps (Immich included) will be briefly unavailable.",
      [
        { label: "Cancel", onClick: hideModal },
        {
          primary: true,
          label: "Reboot now",
          onClick: async () => {
            hideModal();
            await api("/api/reboot", { method: "POST" });
          },
        },
      ]
    );
  };

  el.btnSave.onclick = () => {
    if (state.stagedChanges.size === 0) {
      showModal("Nothing to save", "No settings have been changed.", [
        { label: "OK", primary: true, onClick: hideModal },
      ]);
      return;
    }

    const changeList = Array.from(state.stagedChanges.entries());
    const summary = changeList
      .map(([name, value]) => `<div>${name} &rarr; <b>${value}</b></div>`)
      .join("");

    showModal(
      "Save these changes?",
      summary,
      [
        { label: "Cancel", onClick: hideModal },
        {
          primary: true,
          label: "Save Changes",
          onClick: async () => {
            hideModal();
            await applyChanges(changeList);
          },
        },
      ]
    );
  };

  async function applyChanges(changeList) {
    const payload = {
      changes: changeList.map(([name, value]) => ({ name, value })),
    };
    let resp;
    try {
      resp = await api("/api/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      showModal("Failed to reach the NAS", String(err.message || err), [
        { label: "OK", primary: true, onClick: hideModal },
      ]);
      return;
    }

    const lines = resp.results
      .map(
        (r) =>
          `<div class="result-line ${r.ok ? "ok" : "error"}">${r.ok ? "✓" : "✗"} ${r.name}${
            r.error ? " - " + r.error : ""
          }</div>`
      )
      .join("");

    state.stagedChanges.clear();
    await refreshAttributes();

    const rebootActions = [{ label: "Close", onClick: hideModal }];
    if (resp.pending_reboot) {
      rebootActions.push({
        primary: true,
        label: "Reboot Now",
        onClick: async () => {
          hideModal();
          await api("/api/reboot", { method: "POST" });
        },
      });
    }

    showModal(
      resp.pending_reboot ? "Changes saved - reboot required" : "Changes saved",
      lines +
        (resp.pending_reboot
          ? '<p style="color:#ffd452;margin-top:10px">A reboot is required for these changes to take effect.</p>'
          : ""),
      rebootActions
    );
  }

  async function refreshAttributes() {
    const attrsResp = await api("/api/attributes");
    state.attributes = attrsResp.attributes;
    state.passwordStatus = attrsResp.password_status;
    state.pendingReboot = attrsResp.pending_reboot;
    renderSettings();
    renderPendingBanner();
  }

  loadAll().catch((err) => {
    el.settings.innerHTML = `<div class="loading" style="color:#ff6b6b">Failed to load: ${err.message}</div>`;
  });
})();
