(() => {
  "use strict";

  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");

  const uniqueSorted = (values) =>
    [...new Set(values.filter((value) => value !== null && value !== undefined && value !== ""))]
      .sort((left, right) => String(left).localeCompare(String(right)));

  const optionMarkup = (values, label) =>
    [`<option value="">${escapeHtml(label)}</option>`]
      .concat(values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`))
      .join("");

  const sourceMarkup = (sources) => {
    if (!sources || !sources.length) return "<p>没有登记来源。</p>";
    return `<ul>${sources
      .map((source) => {
        const label = source.source_id || source.name || "来源";
        return source.url
          ? `<li><a href="${escapeHtml(source.url)}" target="_blank" rel="noopener">${escapeHtml(label)}</a></li>`
          : `<li>${escapeHtml(label)}</li>`;
      })
      .join("")}</ul>`;
  };

  async function initializeExplorer(root) {
    if (root.dataset.initialized === "true") return;
    root.dataset.initialized = "true";
    const indexUrl = root.dataset.queryIndex || "../query-index.json";
    let payload;
    try {
      const response = await fetch(indexUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      payload = await response.json();
    } catch (error) {
      root.innerHTML = `<p class="ckb-error">查询索引载入失败：${escapeHtml(error.message)}</p>`;
      return;
    }

    const entities = payload.entities || [];
    const relationships = payload.relationships || [];
    const facts = new Map((payload.facts || []).map((fact) => [fact.id, fact]));
    const entityMap = new Map(entities.map((entity) => [entity.id, entity]));
    const incident = new Map();
    for (const relationship of relationships) {
      if (!incident.has(relationship.source_id)) incident.set(relationship.source_id, []);
      if (!incident.has(relationship.target_id)) incident.set(relationship.target_id, []);
      incident.get(relationship.source_id).push(relationship);
      if (relationship.target_id !== relationship.source_id) {
        incident.get(relationship.target_id).push(relationship);
      }
    }

    root.innerHTML = `
      <section class="ckb-filter-panel" aria-label="高级筛选">
        <label>全文检索<input data-filter="text" type="search" placeholder="名称、别名或标签"></label>
        <label>实体类型<select data-filter="entity_type"></select></label>
        <label>领域<select data-filter="domain"></select></label>
        <label>类别<select data-filter="class"></select></label>
        <label>子类<select data-filter="subclass"></select></label>
        <label>时代<select data-filter="era"></select></label>
        <label>标签<select data-filter="tag"></select></label>
        <label>审核状态<select data-filter="review_status"></select></label>
        <label>技术字段<select data-filter="technical_field"></select></label>
        <label>最少来源数<input data-filter="minimum_sources" type="number" min="0" value="0"></label>
        <label class="ckb-check"><input data-filter="has_technical" type="checkbox">仅显示有技术档案</label>
        <button type="button" data-action="clear-filters">清空筛选</button>
      </section>
      <p class="ckb-query-summary" aria-live="polite"></p>
      <div class="ckb-workspace">
        <section>
          <h2>查询结果</h2>
          <div class="ckb-results"></div>
        </section>
        <section>
          <h2>可展开关系图</h2>
          <div class="ckb-graph-toolbar">
            <label>方向<select data-graph="direction">
              <option value="both">双向</option>
              <option value="out">出向</option>
              <option value="in">入向</option>
            </select></label>
            <label>谓词<select data-graph="predicate"></select></label>
            <button type="button" data-action="reset-graph">重置图谱</button>
          </div>
          <div class="ckb-graph"><p>从左侧选择一个实体。</p></div>
        </section>
      </div>
      <section class="ckb-evidence" aria-live="polite">
        <h2>事实、断言与来源证据</h2>
        <p>点击实体或关系的“查看证据”。</p>
      </section>
    `;

    const filterOptions = {
      entity_type: uniqueSorted(entities.map((row) => row.entity_type)),
      domain: uniqueSorted(entities.map((row) => row.domain)),
      class: uniqueSorted(entities.map((row) => row.class)),
      subclass: uniqueSorted(entities.map((row) => row.subclass)),
      era: uniqueSorted(entities.flatMap((row) => row.eras || [])),
      tag: uniqueSorted(entities.flatMap((row) => row.tags || [])),
      review_status: uniqueSorted(entities.map((row) => row.review_status)),
      technical_field: uniqueSorted(entities.flatMap((row) => row.technical_fields || [])),
    };
    const labels = {
      entity_type: "全部类型",
      domain: "全部领域",
      class: "全部类别",
      subclass: "全部子类",
      era: "全部时代",
      tag: "全部标签",
      review_status: "全部状态",
      technical_field: "全部技术字段",
    };
    for (const [name, values] of Object.entries(filterOptions)) {
      root.querySelector(`[data-filter="${name}"]`).innerHTML = optionMarkup(values, labels[name]);
    }
    root.querySelector('[data-graph="predicate"]').innerHTML = optionMarkup(
      uniqueSorted(relationships.map((row) => row.predicate)),
      "全部谓词"
    );

    const resultsNode = root.querySelector(".ckb-results");
    const summaryNode = root.querySelector(".ckb-query-summary");
    const graphNode = root.querySelector(".ckb-graph");
    const evidenceNode = root.querySelector(".ckb-evidence");
    let selectedEntityId = null;

    const currentFilters = () => {
      const values = {};
      for (const node of root.querySelectorAll("[data-filter]")) {
        values[node.dataset.filter] = node.type === "checkbox" ? node.checked : node.value;
      }
      return values;
    };

    const matches = (entity, filters) => {
      const text = filters.text.trim().toLocaleLowerCase();
      const haystack = [
        entity.id,
        entity.name_en,
        entity.name_zh,
        ...(entity.tags || []),
      ]
        .join(" ")
        .toLocaleLowerCase();
      if (text && !haystack.includes(text)) return false;
      for (const field of ["entity_type", "domain", "class", "subclass", "review_status"]) {
        if (filters[field] && entity[field] !== filters[field]) return false;
      }
      if (filters.era && !(entity.eras || []).includes(filters.era)) return false;
      if (filters.tag && !(entity.tags || []).includes(filters.tag)) return false;
      if (
        filters.technical_field &&
        !(entity.technical_fields || []).includes(filters.technical_field)
      ) return false;
      if (Number(entity.source_count || 0) < Number(filters.minimum_sources || 0)) return false;
      if (filters.has_technical && !(entity.technical_fields || []).length) return false;
      return true;
    };

    const renderEntityEvidence = (entity) => {
      const related = incident.get(entity.id) || [];
      evidenceNode.innerHTML = `
        <h2>实体来源证据</h2>
        <p><strong>${escapeHtml(entity.name_zh || entity.name_en)}</strong> · <code>${escapeHtml(entity.id)}</code></p>
        <p>审核状态：${escapeHtml(entity.review_status)}；来源数：${escapeHtml(entity.source_count)}；关联断言：${related.length}</p>
        ${sourceMarkup(entity.sources)}
      `;
    };

    const renderRelationshipEvidence = (relationship) => {
      const fact = facts.get(relationship.fact_id);
      const assertions = fact?.assertions || [relationship];
      const sources = fact?.sources || relationship.provenance?.sources || [];
      evidenceNode.innerHTML = `
        <h2>规范事实 → 原始断言 → 来源</h2>
        <p><code>${escapeHtml(fact?.id || relationship.fact_id || "未聚合")}</code></p>
        <p>${escapeHtml(relationship.source_id)} <strong>${escapeHtml(relationship.predicate)}</strong> ${escapeHtml(relationship.target_id)}</p>
        <details open>
          <summary>原始断言（${assertions.length}）</summary>
          <pre><code>${escapeHtml(JSON.stringify(assertions, null, 2))}</code></pre>
        </details>
        <h3>来源证据</h3>
        ${sourceMarkup(sources)}
      `;
    };

    const graphRelations = (entityId) => {
      const direction = root.querySelector('[data-graph="direction"]').value;
      const predicate = root.querySelector('[data-graph="predicate"]').value;
      return (incident.get(entityId) || []).filter((relationship) => {
        if (predicate && relationship.predicate !== predicate) return false;
        if (direction === "out" && relationship.source_id !== entityId) return false;
        if (direction === "in" && relationship.target_id !== entityId) return false;
        return true;
      });
    };

    const makeGraphNode = (entityId, path) => {
      const entity = entityMap.get(entityId);
      const wrapper = document.createElement("div");
      wrapper.className = "ckb-graph-node";
      wrapper.dataset.entityId = entityId;
      if (!entity) {
        wrapper.textContent = entityId;
        return wrapper;
      }
      wrapper.innerHTML = `
        <div class="ckb-node-card">
          <strong>${escapeHtml(entity.name_zh || entity.name_en)}</strong>
          <code>${escapeHtml(entity.id)}</code>
          <button type="button" data-action="entity-evidence">查看证据</button>
        </div>
        <div class="ckb-graph-children"></div>
      `;
      wrapper.querySelector('[data-action="entity-evidence"]').addEventListener("click", () =>
        renderEntityEvidence(entity)
      );
      const children = wrapper.querySelector(".ckb-graph-children");
      for (const relationship of graphRelations(entityId)) {
        const outgoing = relationship.source_id === entityId;
        const neighborId = outgoing ? relationship.target_id : relationship.source_id;
        const neighbor = entityMap.get(neighborId);
        const row = document.createElement("div");
        row.className = "ckb-edge-row";
        row.dataset.relationshipId = relationship.id;
        row.innerHTML = `
          <span class="ckb-edge-label">${outgoing ? "→" : "←"} ${escapeHtml(relationship.predicate)}</span>
          <button type="button" data-action="edge-evidence">证据</button>
          <button type="button" data-action="expand" ${path.has(neighborId) ? "disabled" : ""}>
            展开 ${escapeHtml(neighbor?.name_zh || neighbor?.name_en || neighborId)}
          </button>
          <div class="ckb-expanded-node"></div>
        `;
        row.querySelector('[data-action="edge-evidence"]').addEventListener("click", () =>
          renderRelationshipEvidence(relationship)
        );
        const expand = row.querySelector('[data-action="expand"]');
        expand.addEventListener("click", () => {
          const target = row.querySelector(".ckb-expanded-node");
          if (target.childElementCount) {
            target.replaceChildren();
            expand.textContent = `展开 ${neighbor?.name_zh || neighbor?.name_en || neighborId}`;
            return;
          }
          target.appendChild(makeGraphNode(neighborId, new Set([...path, neighborId])));
          expand.textContent = "收起";
        });
        children.appendChild(row);
      }
      if (!children.childElementCount) {
        children.innerHTML = "<p class=\"ckb-muted\">当前方向和谓词下没有关系。</p>";
      }
      return wrapper;
    };

    const renderGraph = () => {
      graphNode.replaceChildren();
      if (!selectedEntityId) {
        graphNode.innerHTML = "<p>从左侧选择一个实体。</p>";
        return;
      }
      graphNode.appendChild(makeGraphNode(selectedEntityId, new Set([selectedEntityId])));
    };

    const selectEntity = (entityId) => {
      selectedEntityId = entityId;
      renderGraph();
      renderEntityEvidence(entityMap.get(entityId));
    };

    const renderResults = () => {
      const filters = currentFilters();
      const matched = entities.filter((entity) => matches(entity, filters));
      summaryNode.textContent = `命中 ${matched.length} / ${entities.length} 个实体；本地契约 ${payload.contract?.version || payload.schema_version}。`;
      resultsNode.replaceChildren();
      for (const entity of matched.slice(0, 100)) {
        const card = document.createElement("article");
        card.className = "ckb-result-card";
        card.dataset.entityId = entity.id;
        card.innerHTML = `
          <h3>${escapeHtml(entity.name_zh || entity.name_en)}</h3>
          <p>${escapeHtml(entity.name_en)} · ${escapeHtml(entity.entity_type)} · ${escapeHtml(entity.class || "")}</p>
          <p><code>${escapeHtml(entity.id)}</code></p>
          <div>
            <button type="button" data-action="select">在图谱中展开</button>
            <a href="${escapeHtml(entity.href)}">实体详情</a>
          </div>
        `;
        card.querySelector('[data-action="select"]').addEventListener("click", () =>
          selectEntity(entity.id)
        );
        resultsNode.appendChild(card);
      }
      if (matched.length > 100) {
        const note = document.createElement("p");
        note.className = "ckb-muted";
        note.textContent = "结果超过 100 条；请继续缩小筛选范围。";
        resultsNode.appendChild(note);
      }
    };

    root.addEventListener("input", (event) => {
      if (event.target.matches("[data-filter]")) renderResults();
    });
    root.addEventListener("change", (event) => {
      if (event.target.matches("[data-filter]")) renderResults();
      if (event.target.matches("[data-graph]")) renderGraph();
    });
    root.querySelector('[data-action="clear-filters"]').addEventListener("click", () => {
      for (const node of root.querySelectorAll("[data-filter]")) {
        if (node.type === "checkbox") node.checked = false;
        else if (node.dataset.filter === "minimum_sources") node.value = "0";
        else node.value = "";
      }
      renderResults();
    });
    root.querySelector('[data-action="reset-graph"]').addEventListener("click", renderGraph);
    renderResults();
  }

  const boot = () => {
    const root = document.getElementById("ckb-explorer");
    if (root) initializeExplorer(root);
  };
  if (typeof document$ !== "undefined") document$.subscribe(boot);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
