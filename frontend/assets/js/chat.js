// Handles chat send/receive, rendering messages, and the metadata filter panel.

const Chat = {

  sessionId: "session-" + Date.now(),


  // ─────────────────────────────────────────────────────────────────────────
  // INITIALISATION
  // ─────────────────────────────────────────────────────────────────────────

  bind() {

    document
      .getElementById("send-btn")
      .addEventListener("click", () => this.send());


    document
      .getElementById("chat-input")
      .addEventListener("keydown", (e) => {

        if (e.key === "Enter") {
          this.send();
        }

      });

    // Bind filter panel controls
    FilterPanel.bind();

  },


  // ─────────────────────────────────────────────────────────────────────────
  // SESSION MANAGEMENT
  // ─────────────────────────────────────────────────────────────────────────

  newSession() {
    this.sessionId = "session-" + Date.now();
    document.getElementById("messages").innerHTML = "";
    
    // Deselect any active session elements in the sidebar
    document.querySelectorAll("#session-list li").forEach(el => {
      el.classList.remove("active");
    });
    
    this.renderMessage("assistant", "Hello! Start a new conversation by typing a message below.");
  },

  async loadSession(sessionId) {
    this.sessionId = sessionId;
    const container = document.getElementById("messages");
    container.innerHTML = "<div class='message assistant'>Loading history...</div>";
    
    try {
      const result = await Api.getSessionMessages(sessionId);
      container.innerHTML = "";
      if (result.status === "success") {
        if (result.data.length === 0) {
          this.renderMessage("assistant", "This session has no messages.");
        } else {
          result.data.forEach(msg => {
            this.renderMessage(msg.role, msg.content);
          });
        }
      } else {
        this.renderMessage("assistant", `Failed to load messages: ${result.message}`);
      }
    } catch (e) {
      console.error(e);
      this.renderMessage("assistant", `Error loading session: ${e.message}`);
    }
  },


  // ─────────────────────────────────────────────────────────────────────────
  // SEND MESSAGE
  // ─────────────────────────────────────────────────────────────────────────

  async send() {

    const input = document.getElementById("chat-input");
    const query = input.value.trim();
    if (!query) return;

    // Show user message
    this.renderMessage("user", query);
    input.value = "";

    // Get selected collection
    const activeCollection = UI.getActiveCollection();

    // Get RAG toggle value
    const useDocument = document.getElementById("rag-toggle").checked;

    // Get current filter spec from the filter panel
    const filters = FilterPanel.buildFilters();

    // Call backend
    try {

      const result = await Api.sendChat(
        query,
        this.sessionId,
        activeCollection,
        useDocument,
        filters
      );

      if (result.status === "success") {

        const isNewSession = !document.querySelector(`#session-list li[data-id="${this.sessionId}"]`);

        this.renderMessage("assistant", result.data.answer);

        if (isNewSession) {
          UI.loadSessions();
        }

      } else {
        this.renderMessage("assistant", `Error: ${result.message}`);
      }

    } catch (error) {

      console.error("Chat error:", error);
      this.renderMessage(
        "assistant",
        `⚠️ Could not reach the backend. Make sure the FastAPI server is running at http://localhost:8000. (${error.message})`
      );

    }

  },


  // ─────────────────────────────────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────────────────────────────────

  renderMessage(role, text) {

    const container = document.getElementById("messages");

    const bubble = document.createElement("div");
    bubble.className = `message ${role}`;
    bubble.textContent = text;

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;

  },


};


// ═══════════════════════════════════════════════════════════════════════════
// FILTER PANEL — metadata-based Qdrant filter builder
// ═══════════════════════════════════════════════════════════════════════════

const FilterPanel = {

  /**
   * Attach all event listeners for the filter panel UI.
   */
  bind() {
    // Toggle open/close
    document.getElementById("filter-toggle-btn").addEventListener("click", () => this.toggle());

    // Add a new blank filter row
    document.getElementById("filter-add-btn").addEventListener("click", () => this.addRow());

    // Clear all rows
    document.getElementById("filter-clear-btn").addEventListener("click", () => this.clearAll());
  },

  // ── Open / close ──────────────────────────────────────────────────────────

  toggle() {
    const wrapper = document.getElementById("filter-panel-wrapper");
    const btn     = document.getElementById("filter-toggle-btn");
    const isOpen  = wrapper.classList.toggle("open");
    btn.setAttribute("aria-expanded", isOpen);
  },

  // ── Row management ────────────────────────────────────────────────────────

  /**
   * Add a new filter row to the container.
   * Each row has: clause select | field input | match-type select | value input | remove button
   */
  addRow(defaults = {}) {
    const container = document.getElementById("filter-rows-container");

    const row = document.createElement("div");
    row.className = "filter-row";
    row.dataset.filterRow = "true";

    // ── Clause selector (must / must_not / should) ──
    const clauseSel = document.createElement("select");
    clauseSel.className = "filter-clause-select";
    clauseSel.title = "Filter clause";
    [
      { value: "must",     label: "MUST" },
      { value: "must_not", label: "MUST NOT" },
      { value: "should",   label: "SHOULD" },
    ].forEach(({ value, label }) => {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = label;
      if (defaults.clause === value) opt.selected = true;
      clauseSel.appendChild(opt);
    });

    // ── Metadata field name ──
    const fieldInput = document.createElement("input");
    fieldInput.type = "text";
    fieldInput.className = "filter-field-input";
    fieldInput.placeholder = "field (e.g. source)";
    fieldInput.title = "Payload field name";
    if (defaults.key) fieldInput.value = defaults.key;

    // ── Match type selector ──
    const typeSel = document.createElement("select");
    typeSel.className = "filter-type-select";
    typeSel.title = "Match type";
    [
      { value: "match",     label: "=" },
      { value: "match_any", label: "in [ ]" },
    ].forEach(({ value, label }) => {
      const opt = document.createElement("option");
      opt.value = value;
      opt.textContent = label;
      if (defaults.type === value) opt.selected = true;
      typeSel.appendChild(opt);
    });

    // ── Value input ──
    const valueInput = document.createElement("input");
    valueInput.type = "text";
    valueInput.className = "filter-value-input";
    valueInput.title = "Filter value";
    if (defaults.value) valueInput.value = defaults.value;

    // Update placeholder when match type changes
    const updatePlaceholder = () => {
      valueInput.placeholder = typeSel.value === "match_any"
        ? "val1, val2, val3"
        : "exact value";
    };
    typeSel.addEventListener("change", updatePlaceholder);
    updatePlaceholder();

    // ── Remove button ──
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "filter-remove-btn";
    removeBtn.title = "Remove this filter";
    removeBtn.textContent = "×";
    removeBtn.addEventListener("click", () => {
      row.remove();
      this._updateBadge();
    });

    // Update badge whenever a field changes
    [clauseSel, fieldInput, typeSel, valueInput].forEach(el => {
      el.addEventListener("input",  () => this._updateBadge());
      el.addEventListener("change", () => this._updateBadge());
    });

    row.appendChild(clauseSel);
    row.appendChild(fieldInput);
    row.appendChild(typeSel);
    row.appendChild(valueInput);
    row.appendChild(removeBtn);
    container.appendChild(row);

    this._updateBadge();
    fieldInput.focus();
  },

  clearAll() {
    document.getElementById("filter-rows-container").innerHTML = "";
    this._updateBadge();
  },

  // ── Build filter object ───────────────────────────────────────────────────

  /**
   * Read all filter rows and build a SearchFilters-compatible JSON object:
   * {
   *   must:     [ { key, match } | { key, match_any } ],
   *   must_not: [ ... ],
   *   should:   [ ... ],
   * }
   *
   * Rows with an empty field or value are silently skipped.
   * Returns null when no valid conditions exist.
   */
  buildFilters() {
    const rows = document.querySelectorAll("[data-filter-row='true']");
    const result = { must: [], must_not: [], should: [] };
    let hasAny = false;

    rows.forEach(row => {
      const clause     = row.querySelector(".filter-clause-select").value;
      const key        = row.querySelector(".filter-field-input").value.trim();
      const matchType  = row.querySelector(".filter-type-select").value;
      const rawValue   = row.querySelector(".filter-value-input").value.trim();

      if (!key || !rawValue) return;   // skip incomplete rows

      let condition;
      if (matchType === "match_any") {
        // Comma-separated list → array
        const values = rawValue.split(",").map(v => v.trim()).filter(Boolean);
        if (!values.length) return;
        condition = { key, match_any: values };
      } else {
        condition = { key, match: rawValue };
      }

      result[clause].push(condition);
      hasAny = true;
    });

    return hasAny ? result : null;
  },

  // ── Badge / indicator update ──────────────────────────────────────────────

  /**
   * Re-counts filled rows and updates the badge, pulsing dot, and wrapper outline.
   */
  _updateBadge() {
    const rows = document.querySelectorAll("[data-filter-row='true']");
    let count = 0;
    rows.forEach(row => {
      const key   = row.querySelector(".filter-field-input").value.trim();
      const value = row.querySelector(".filter-value-input").value.trim();
      if (key && value) count++;
    });

    const badge   = document.getElementById("filter-count-badge");
    const dot     = document.getElementById("filter-active-dot");
    const wrapper = document.getElementById("filter-panel-wrapper");

    if (count > 0) {
      badge.textContent = count;
      badge.classList.add("visible");
      dot.classList.add("visible");
      wrapper.classList.add("has-filters");
    } else {
      badge.classList.remove("visible");
      dot.classList.remove("visible");
      wrapper.classList.remove("has-filters");
    }
  },

};