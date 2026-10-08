// Frontend logic for JOB_APP_AUTO (Dark Uncluttered Edition: Auto-Discovery + Manual Paste + Semi-Auto Tracker + Slide Prep)

let candidateProfile = {};
let platformsList = [];
let historyRecords = [];
let availableStatuses = [];
let currentStatusFilter = "All";
let currentView = "evaluate";
let currentDiscoveryMode = "auto";
let selectedDiscoverPlatform = "all";
let discoveredJobsCache = [];

document.addEventListener("DOMContentLoaded", async () => {
    // Close quick-copy dropdown when clicking outside
    document.addEventListener("click", () => {
        const menu = document.getElementById("quick-copy-menu");
        if (menu && !menu.classList.contains("hidden")) {
            menu.classList.add("hidden");
        }
    });

    await Promise.all([
        loadProfile(),
        loadLLMStatus(),
        loadPlatforms(),
        loadHistory(),
    ]);

    // Load initial discovered jobs preview (without writing to CSV until user clicks Auto-Find or Save)
    await runAutoDiscovery(false);
});

// --- View & Mode Navigation ---

function switchView(viewName) {
    currentView = viewName;
    const views = ["evaluate", "applications", "prep"];
    views.forEach((v) => {
        const section = document.getElementById(`view-${v}`);
        const navBtn = document.getElementById(`nav-btn-${v}`);
        if (section) section.classList.toggle("active", v === viewName);
        if (navBtn) navBtn.classList.toggle("active", v === viewName);
    });
}

function switchDiscoveryMode(mode) {
    currentDiscoveryMode = mode;
    const autoPanel = document.getElementById("subview-auto-discover");
    const manualPanel = document.getElementById("subview-manual-paste");
    const btnAuto = document.getElementById("mode-btn-auto");
    const btnManual = document.getElementById("mode-btn-manual");

    if (autoPanel) autoPanel.classList.toggle("hidden", mode !== "auto");
    if (manualPanel) manualPanel.classList.toggle("hidden", mode !== "manual");
    if (btnAuto) btnAuto.classList.toggle("active", mode === "auto");
    if (btnManual) btnManual.classList.toggle("active", mode === "manual");
}

function toggleQuickCopyMenu(event) {
    event.stopPropagation();
    const menu = document.getElementById("quick-copy-menu");
    if (menu) menu.classList.toggle("hidden");
}

function openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.remove("hidden");
}

function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.classList.add("hidden");
}

function showToast(message) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.remove("hidden");
    setTimeout(() => {
        toast.classList.add("hidden");
    }, 2600);
}

async function copyToClipboard(text, label = "Copied") {
    try {
        await navigator.clipboard.writeText(text);
        showToast(`${label} copied to clipboard`);
    } catch (err) {
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        showToast(`${label} copied to clipboard`);
    }
}

// --- Profile & AI Engine Status ---

async function loadProfile() {
    try {
        const res = await fetch("/api/profile");
        candidateProfile = await res.json();
        const nameEl = document.getElementById("profile-name");
        if (nameEl && candidateProfile.name) nameEl.textContent = candidateProfile.name;
    } catch (e) {
        console.error("Failed to load profile", e);
    }
}

async function loadLLMStatus() {
    try {
        const res = await fetch("/api/llm/status");
        const data = await res.json();
        updateLLMBadgeUI(data);
    } catch (e) {
        console.error("Failed to load LLM status", e);
    }
}

function updateLLMBadgeUI(data) {
    const badge = document.getElementById("llm-engine-badge");
    if (!badge) return;
    if (data.provider === "openai" && data.has_openai_key) {
        badge.textContent = `AI Scorer: OpenAI (${data.openai_model})`;
    } else if (data.provider === "ollama") {
        badge.textContent = `AI Scorer: Ollama (${data.ollama_model})`;
    } else {
        badge.textContent = "AI Scorer: Ready (No API Key Needed)";
    }

    const provSel = document.getElementById("cfg-llm-provider");
    const ollamaMod = document.getElementById("cfg-ollama-model");
    if (provSel && data.provider) provSel.value = data.provider;
    if (ollamaMod && data.ollama_model) ollamaMod.value = data.ollama_model;
}

async function saveAISettings() {
    const provider = document.getElementById("cfg-llm-provider")?.value || "auto";
    const ollamaModel = document.getElementById("cfg-ollama-model")?.value || "llama3.2";
    const openaiKey = document.getElementById("cfg-openai-key")?.value || "";

    try {
        const res = await fetch("/api/llm/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                provider,
                ollama_model: ollamaModel,
                openai_api_key: openaiKey || null,
            }),
        });
        const updated = await res.json();
        updateLLMBadgeUI(updated);
        closeModal("ai-settings-modal");
        showToast("AI scoring engine updated");
    } catch (e) {
        console.error("Failed to update AI config", e);
    }
}

// --- Automated Multi-Platform Job Discovery (No Link Pasting Required) ---

function togglePlatformFilter(platId) {
    selectedDiscoverPlatform = platId;
    document.querySelectorAll(".plat-chip").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.plat === platId);
    });
    runAutoDiscovery(false);
}

async function runAutoDiscovery(userTriggered = true) {
    const keywords = document.getElementById("discover-keywords")?.value || "AI Engineer, Machine Learning, Python";
    const threshold = parseInt(document.getElementById("discover-threshold")?.value || "65", 10);
    const autoSaveBox = document.getElementById("auto-save-considering");
    const shouldAutoSave = userTriggered ? (autoSaveBox ? autoSaveBox.checked : true) : false;
    const minSal = parseInt(document.getElementById("min-salary")?.value || "40000", 10);
    const maxSal = parseInt(document.getElementById("max-salary")?.value || "45000", 10);

    const platforms = selectedDiscoverPlatform === "all"
        ? ["linkedin", "jobsdb", "jobthai", "jobbkk", "jobtopgun", "workventure"]
        : [selectedDiscoverPlatform];

    const btn = document.getElementById("btn-run-discovery");
    if (btn && userTriggered) {
        btn.disabled = true;
        btn.textContent = "⏳ Scanning & Scoring Jobs...";
    }

    try {
        const res = await fetch("/api/pipeline/auto-discover", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                keywords,
                platforms,
                location: "Bangkok",
                min_salary: minSal,
                max_salary: maxSal,
                min_score_threshold: threshold,
                auto_save_considering: shouldAutoSave,
                max_results: 12,
            }),
        });
        const data = await res.json();
        discoveredJobsCache = data.jobs || [];
        renderDiscoveredJobs(data);

        if (shouldAutoSave && data.newly_saved_count > 0) {
            await loadHistory();
            showToast(`Found ${data.total_found} jobs · Added ${data.newly_saved_count} matches to 'Considering'`);
        } else if (userTriggered) {
            await loadHistory();
            showToast(`Scored ${data.total_found} jobs (${data.compatible_count} compatible matches)`);
        }
    } catch (e) {
        console.error("Auto-discovery failed", e);
        showToast("Error running auto-discovery");
    } finally {
        if (btn && userTriggered) {
            btn.disabled = false;
            btn.textContent = "⚡ Auto-Find & Score Jobs";
        }
    }
}

function renderDiscoveredJobs(data) {
    const summaryBar = document.getElementById("discovery-summary-bar");
    if (summaryBar) {
        summaryBar.classList.remove("hidden");
        document.getElementById("disc-total-count").textContent = data.total_found;
        document.getElementById("disc-compat-count").textContent = data.compatible_count;
        document.getElementById("disc-saved-count").textContent =
            data.newly_saved_count + data.already_in_history_count;
        const engLabel = document.getElementById("disc-engine-label");
        if (engLabel) {
            engLabel.textContent = `Engine: ${data.engine_used === "smart_profile_matcher" ? "Built-in Profile Matcher (No Key Needed)" : data.engine_used}`;
        }
    }

    const container = document.getElementById("discovered-jobs-container");
    if (!container) return;

    if (!data.jobs || data.jobs.length === 0) {
        container.innerHTML = `<div class="empty-card"><p>No matching jobs found for these filters. Try broadening keywords.</p></div>`;
        return;
    }

    container.innerHTML = data.jobs
        .map((job, idx) => {
            const ev = job.evaluation;
            const scoreClass = ev.overall_score >= 80 ? "high" : ev.overall_score >= 65 ? "medium" : "low";
            const isSaved = job.saved_to_considering || job.already_in_history;

            const skillsHtml = (ev.matched_skills || [])
                .slice(0, 5)
                .map((s) => `<span class="skill-chip">✓ ${escapeHtml(s)}</span>`)
                .join("");

            const statusBadgeHtml = isSaved
                ? `<span class="meta-tag considering-tag">✓ In 'Considering'</span>`
                : `<button type="button" class="btn-amber-sm" onclick="saveSingleDiscoveredJob(${idx})">+ Save to Considering</button>`;

            const markSubmittedBtn = job.record_id
                ? `<button type="button" class="btn-emerald-sm" onclick="quickMarkSubmitted(${job.record_id}, '${escapeQuotes(job.company_name)}')">✓ Mark Submitted</button>`
                : "";

            return `
            <article class="job-card">
                <div>
                    <div class="job-card-top">
                        <div>
                            <h3 class="job-title">${escapeHtml(job.job_position)}</h3>
                            <div class="job-company">${escapeHtml(job.company_name)} · ${escapeHtml(job.location)}</div>
                        </div>
                        <div class="score-pill ${scoreClass}" title="${escapeHtml(ev.verdict_label)}">
                            ${ev.overall_score}% Match
                        </div>
                    </div>

                    <div class="job-meta-row" style="margin-top:0.65rem;">
                        <span class="meta-tag plat">${escapeHtml(job.platform_name)}</span>
                        <span class="meta-tag">💰 ${escapeHtml(job.salary_tag)}</span>
                        ${job.industry ? `<span class="meta-tag">${escapeHtml(job.industry)}</span>` : ""}
                    </div>

                    <div class="job-subscores" style="margin-top:0.6rem;">
                        <span>Resume Skills: <strong>${ev.skill_match_score}%</strong></span>
                        <span>Goal Fit: <strong>${ev.goal_alignment_score}%</strong></span>
                        <span>Salary Fit: <strong>${ev.salary_fit_score}%</strong></span>
                    </div>

                    <div class="job-skills-row" style="margin-top:0.6rem;">
                        ${skillsHtml}
                    </div>
                </div>

                <div class="job-card-actions">
                    <div class="job-card-actions-left">
                        ${statusBadgeHtml}
                        ${markSubmittedBtn}
                    </div>
                    <div class="job-card-actions-right">
                        <button type="button" class="btn-ghost-sm" onclick="openCoverLetterModal(${idx})">
                            📄 Cover Letter
                        </button>
                        <a href="${escapeHtml(job.link)}" target="_blank" class="btn-outline-sm">
                            Open Job ↗
                        </a>
                    </div>
                </div>
            </article>
            `;
        })
        .join("");
}

function openCoverLetterModal(index) {
    const job = discoveredJobsCache[index];
    if (!job) return;
    document.getElementById("modal-cl-title").textContent = `Cover Letter — ${job.company_name}`;
    document.getElementById("modal-cl-sub").textContent = `${job.job_position} (${job.evaluation.overall_score}% Profile Match)`;
    document.getElementById("modal-cl-textarea").value = job.cover_letter || "";
    openModal("cover-letter-modal");
}

function copyModalCoverLetter() {
    const text = document.getElementById("modal-cl-textarea")?.value || "";
    if (text) copyToClipboard(text, "Cover Letter");
}

async function saveSingleDiscoveredJob(index) {
    const job = discoveredJobsCache[index];
    if (!job) return;
    const minSal = parseInt(document.getElementById("min-salary")?.value || "40000", 10);
    const maxSal = parseInt(document.getElementById("max-salary")?.value || "45000", 10);

    try {
        const res = await fetch("/api/pipeline/shortlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                company_name: job.company_name,
                job_position: job.job_position,
                job_description: job.job_description,
                link: job.link,
                platform: job.platform,
                industry: job.industry || "",
                location: job.location || "Bangkok, Thailand",
                priority: job.evaluation.overall_score >= 82 ? "First" : "Second",
                min_salary: minSal,
                max_salary: maxSal,
                auto_save_if_compatible: true,
                force_save: true,
            }),
        });
        const data = await res.json();
        job.saved_to_considering = true;
        if (data.record && data.record.id) {
            job.record_id = data.record.id;
        }
        renderDiscoveredJobs({
            total_found: discoveredJobsCache.length,
            compatible_count: discoveredJobsCache.filter((j) => j.evaluation.is_compatible).length,
            newly_saved_count: discoveredJobsCache.filter((j) => j.saved_to_considering).length,
            already_in_history_count: discoveredJobsCache.filter((j) => j.already_in_history).length,
            engine_used: "smart_profile_matcher",
            jobs: discoveredJobsCache,
        });
        await loadHistory();
        showToast(`Saved ${job.company_name} as 'Considering'`);
    } catch (e) {
        console.error("Failed saving job", e);
    }
}

// --- Quick Copy & Salary Helpers ---

function copyField(fieldKey) {
    const minSal = parseInt(document.getElementById("min-salary")?.value || 40000, 10);
    const maxSal = parseInt(document.getElementById("max-salary")?.value || 45000, 10);

    const map = {
        name_en: candidateProfile.name || "Kwankhao Sivasomboon",
        email: candidateProfile.email || "Kwankhaosiva@gmail.com",
        phone: candidateProfile.phone || "095-959-6921",
        salary_en: `${minSal.toLocaleString()} - ${maxSal.toLocaleString()} THB (Negotiable)`,
        resume_pdf: candidateProfile.resume_pdf_path || "",
        portfolio: candidateProfile.portfolio_url || "https://kwankhaosiva-repo.github.io/Kwankhao_WebCVPort",
    };

    copyToClipboard(map[fieldKey] || "", fieldKey.toUpperCase());
}

function setSalaryPreset(minVal, maxVal) {
    document.getElementById("min-salary").value = minVal;
    document.getElementById("max-salary").value = maxVal;
    updateSalaryExpectation();
}

function updateSalaryExpectation() {
    const minSal = parseInt(document.getElementById("min-salary").value || 40000, 10);
    const maxSal = parseInt(document.getElementById("max-salary").value || 45000, 10);
    const chipEn = document.getElementById("chip-salary-en");
    if (chipEn) chipEn.textContent = `${minSal.toLocaleString()} - ${maxSal.toLocaleString()} THB`;
}

// --- Manual Paste Subview Logic (Kept Intact) ---

async function loadPlatforms() {
    try {
        const res = await fetch("/api/platforms");
        platformsList = await res.json();
        const container = document.getElementById("platforms-grid");
        if (!container) return;
        container.innerHTML = platformsList
            .map(
                (p) => `
            <button type="button" class="btn-outline-sm" onclick="searchOnPlatform('${p.id}')">
                ${escapeHtml(p.name)} ↗
            </button>
        `
            )
            .join("");
    } catch (e) {
        console.error("Failed to load platforms", e);
    }
}

async function searchOnPlatform(platformId) {
    const keywords = document.getElementById("global-search-keywords")?.value || "AI Engineer";
    try {
        const res = await fetch("/api/platforms/search-url", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ platform: platformId, keywords, location: "Bangkok" }),
        });
        const data = await res.json();
        if (data.url) window.open(data.url, "_blank");
    } catch (e) {
        console.error("Platform search error", e);
    }
}

async function evaluateCompatibilityAndCoverLetter() {
    const company = document.getElementById("app-company")?.value.trim() || "Target Company";
    const position = document.getElementById("app-position")?.value.trim() || "AI Engineer";
    const jd = document.getElementById("app-jd")?.value.trim() || "";
    const platform = document.getElementById("app-platform")?.value || "linkedin";
    const link = document.getElementById("app-link")?.value.trim() || "";
    const minSal = parseInt(document.getElementById("min-salary")?.value || 40000, 10);
    const maxSal = parseInt(document.getElementById("max-salary")?.value || 45000, 10);

    try {
        const res = await fetch("/api/compatibility/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                company_name: company,
                job_position: position,
                job_description: jd,
                platform,
                link,
                min_salary: minSal,
                max_salary: maxSal,
            }),
        });
        const evalData = await res.json();
        renderManualCompatibilityUI(evalData);

        if (evalData.suggested_domain) {
            const domSel = document.getElementById("cl-domain");
            if (domSel) domSel.value = evalData.suggested_domain;
        }
        await generateCoverLetter();
        showToast(`Compatibility Score: ${evalData.overall_score}%`);
    } catch (e) {
        console.error("Manual evaluation failed", e);
    }
}

function renderManualCompatibilityUI(data) {
    document.getElementById("compat-overall-score").textContent = `${data.overall_score}%`;
    document.getElementById("compat-verdict-badge").textContent = data.verdict_label;
    document.getElementById("compat-reasoning").textContent = data.reasoning;
    document.getElementById("compat-skill-val").textContent = `${data.skill_match_score}%`;
    document.getElementById("compat-goal-val").textContent = `${data.goal_alignment_score}%`;
    document.getElementById("compat-salary-val").textContent = `${data.salary_fit_score}%`;

    const tagsBox = document.getElementById("compat-skills-tags");
    if (tagsBox) {
        tagsBox.innerHTML = (data.matched_skills || [])
            .map((s) => `<span class="skill-chip">✓ ${escapeHtml(s)}</span>`)
            .join("");
    }
}

async function generateCoverLetter() {
    const company = document.getElementById("app-company")?.value.trim() || "Hiring Company";
    const position = document.getElementById("app-position")?.value.trim() || "AI Engineer";
    const jd = document.getElementById("app-jd")?.value.trim() || "";
    const domain = document.getElementById("cl-domain")?.value || "ai_backend";
    const minSal = parseInt(document.getElementById("min-salary")?.value || 40000, 10);
    const maxSal = parseInt(document.getElementById("max-salary")?.value || 45000, 10);

    try {
        const res = await fetch("/api/cover-letter/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                company_name: company,
                job_position: position,
                job_description: jd,
                target_salary_min: minSal,
                target_salary_max: maxSal,
                focus_domain: domain,
            }),
        });
        const data = await res.json();
        document.getElementById("cover-letter-output").value = data.cover_letter || "";
    } catch (e) {
        console.error("Cover letter error", e);
    }
}

function copyCoverLetter() {
    const text = document.getElementById("cover-letter-output")?.value || "";
    if (text) copyToClipboard(text, "Cover Letter");
}

async function runShortlistPipeline(forceSave = true) {
    const company = document.getElementById("app-company")?.value.trim();
    const position = document.getElementById("app-position")?.value.trim();
    if (!company || !position) {
        showToast("Please enter Company Name and Job Title first");
        return;
    }
    const jd = document.getElementById("app-jd")?.value.trim() || "";
    const link = document.getElementById("app-link")?.value.trim() || "";
    const platform = document.getElementById("app-platform")?.value || "linkedin";
    const priority = document.getElementById("app-priority")?.value || "First";
    const minSal = parseInt(document.getElementById("min-salary")?.value || 40000, 10);
    const maxSal = parseInt(document.getElementById("max-salary")?.value || 45000, 10);

    try {
        const res = await fetch("/api/pipeline/shortlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                company_name: company,
                job_position: position,
                job_description: jd,
                link,
                platform,
                priority,
                min_salary: minSal,
                max_salary: maxSal,
                auto_save_if_compatible: true,
                force_save: forceSave,
            }),
        });
        const result = await res.json();
        renderManualCompatibilityUI(result.evaluation);
        document.getElementById("cover-letter-output").value = result.cover_letter || "";
        await loadHistory();
        showToast(`Saved ${company} as 'Considering'`);
    } catch (e) {
        console.error("Shortlist error", e);
    }
}

// --- View 2: History & Status Management ---

function setStatusFilter(status) {
    currentStatusFilter = status;
    document.querySelectorAll("#status-filter-tabs .filter-pill").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.status === status);
    });
    loadHistory();
}

async function loadHistory() {
    const search = document.getElementById("history-search")?.value || "";
    try {
        const params = new URLSearchParams();
        if (search) params.set("search", search);
        if (currentStatusFilter && currentStatusFilter !== "All") {
            params.set("status", currentStatusFilter);
        }

        const res = await fetch(`/api/history?${params.toString()}`);
        const data = await res.json();
        historyRecords = data.records || [];
        availableStatuses = data.available_statuses || [
            "Considering",
            "Submitted",
            "Resume Sent",
            "HR Contacted",
            "Interview Scheduled",
            "Offer Received",
            "Not Pass?",
        ];

        if (data.stats) {
            document.getElementById("stat-total").textContent = data.stats.total || 0;
            document.getElementById("stat-considering").textContent = data.stats.considering || 0;
            document.getElementById("stat-submitted").textContent = data.stats.submitted || 0;
            document.getElementById("stat-interview").textContent = data.stats.interview_or_contacted || 0;

            const navCons = document.getElementById("nav-considering-count");
            if (navCons) navCons.textContent = data.stats.considering || 0;
            const navSub = document.getElementById("nav-submitted-count");
            if (navSub) navSub.textContent = data.stats.submitted || 0;
        }

        renderHistoryTable();
        await populatePrepDropdown();
    } catch (e) {
        console.error("Failed to load history", e);
    }
}

function renderHistoryTable() {
    const tbody = document.getElementById("history-table-body");
    if (!tbody) return;

    if (!historyRecords.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-secondary);">No applications in this filter yet.</td></tr>`;
        return;
    }

    tbody.innerHTML = historyRecords
        .slice()
        .reverse()
        .map((rec) => {
            const statusClass =
                rec.status === "Considering"
                    ? "status-considering"
                    : rec.status === "Submitted" || rec.status === "Resume Sent"
                    ? "status-submitted"
                    : "";

            const statusOptions = availableStatuses
                .map(
                    (st) =>
                        `<option value="${escapeHtml(st)}" ${rec.status === st ? "selected" : ""}>${escapeHtml(st)}</option>`
                )
                .join("");

            const linkBtn = rec.link
                ? `<a href="${escapeHtml(rec.link)}" target="_blank" class="btn-outline-sm">Open ↗</a>`
                : "";

            const submitBtn =
                rec.status === "Considering"
                    ? `<button type="button" class="btn-emerald-sm" onclick="quickMarkSubmitted(${rec.id}, '${escapeQuotes(rec.company)}')">✓ Mark Submitted</button>`
                    : "";

            return `
            <tr>
                <td style="font-family:var(--font-mono); color:var(--text-secondary);">#${rec.id}</td>
                <td><strong>${escapeHtml(rec.company)}</strong></td>
                <td>${escapeHtml(rec.job_position || "—")}</td>
                <td><span class="meta-tag">${escapeHtml(rec.priority || "First")}</span></td>
                <td>
                    <select class="status-select ${statusClass}" onchange="updateRecordStatus(${rec.id}, this.value)">
                        ${statusOptions}
                    </select>
                </td>
                <td style="font-size:0.78rem; color:var(--text-secondary);">
                    <div>${escapeHtml(rec.salary || rec.offer_salary || "40k-45k THB")}</div>
                    ${rec.notes ? `<div style="color:var(--text-muted);">${escapeHtml(rec.notes.slice(0, 60))}</div>` : ""}
                </td>
                <td>
                    <div style="display:flex; gap:0.4rem; flex-wrap:wrap;">
                        ${linkBtn}
                        ${submitBtn}
                        <button type="button" class="btn-ghost-sm" onclick="prepareSlidesForRecord(${rec.id})">🎯 Prep Slides</button>
                    </div>
                </td>
            </tr>
        `;
        })
        .join("");
}

async function updateRecordStatus(recordId, newStatus) {
    try {
        const res = await fetch("/api/history/status", {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ record_id: recordId, status: newStatus }),
        });
        if (res.ok) {
            showToast(`Updated #${recordId} → ${newStatus}`);
            await loadHistory();
        }
    } catch (e) {
        console.error("Failed to update status", e);
    }
}

async function quickMarkSubmitted(recordId, companyName) {
    await updateRecordStatus(recordId, "Submitted");
    showToast(`${companyName} marked as Submitted!`);
}

// --- View 3: Interview & 5-Slide Presentation Prep ---

async function populatePrepDropdown() {
    const sel = document.getElementById("prep-job-select");
    if (!sel) return;

    try {
        const res = await fetch("/api/history");
        const data = await res.json();
        const allRecs = data.records || [];

        const submitted = allRecs.filter(
            (r) =>
                r.status === "Submitted" ||
                r.status === "Resume Sent" ||
                r.status === "HR Contacted" ||
                r.status === "Interview Scheduled"
        );
        const others = allRecs.filter((r) => !submitted.includes(r));

        let html = `<option value="">— Select Submitted Application —</option>`;
        if (submitted.length) {
            html += `<optgroup label="Submitted & Active (${submitted.length})">`;
            submitted.forEach((r) => {
                html += `<option value="${r.id}">#${r.id} ${escapeHtml(r.company)} — ${escapeHtml(r.job_position || "AI Engineer")} [${r.status}]</option>`;
            });
            html += `</optgroup>`;
        }
        if (others.length) {
            html += `<optgroup label="Considering / Other (${others.length})">`;
            others.forEach((r) => {
                html += `<option value="${r.id}">#${r.id} ${escapeHtml(r.company)} — ${escapeHtml(r.job_position || "AI Engineer")} [${r.status}]</option>`;
            });
            html += `</optgroup>`;
        }
        sel.innerHTML = html;
    } catch (e) {
        console.error("Failed to populate prep dropdown", e);
    }
}

function onSelectPrepJob() {
    const val = document.getElementById("prep-job-select")?.value;
    if (val) generateCompanyPrep(parseInt(val, 10));
}

async function prepareSlidesForRecord(recordId) {
    switchView("prep");
    const sel = document.getElementById("prep-job-select");
    if (sel) sel.value = String(recordId);
    await generateCompanyPrep(recordId);
}

async function generateCompanyPrep(explicitRecordId = null) {
    const selVal = explicitRecordId || parseInt(document.getElementById("prep-job-select")?.value || "0", 10);
    const payload = selVal
        ? { record_id: selVal, company_name: "", job_position: "" }
        : {
              company_name: document.getElementById("app-company")?.value.trim() || "Target Company",
              job_position: document.getElementById("app-position")?.value.trim() || "AI Engineer",
          };

    try {
        const res = await fetch("/api/prep/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const report = await res.json();
        renderPrepReport(report);
        showToast(`5-Slide Deck ready for ${report.company_name}`);
    } catch (e) {
        console.error("Prep error", e);
    }
}

function renderPrepReport(report) {
    document.getElementById("prep-empty-state")?.classList.add("hidden");
    const container = document.getElementById("prep-Result-container");
    if (container) container.classList.remove("hidden");

    document.getElementById("prep-industry-tag").textContent = report.industry_category;
    document.getElementById("prep-company-title").textContent = `${report.company_name} — ${report.job_position}`;
    document.getElementById("prep-company-overview").textContent = report.company_overview;
    document.getElementById("prep-strategic-alignment").textContent = report.strategic_alignment;
    document.getElementById("prep-markdown-raw").value = report.markdown_deck || "";

    const linksBox = document.getElementById("prep-research-links");
    if (linksBox) {
        linksBox.innerHTML = (report.research_links || [])
            .map(
                (l) =>
                    `<a href="${escapeHtml(l.url)}" target="_blank" class="btn-outline-sm">🔎 ${escapeHtml(l.label)} ↗</a>`
            )
            .join("");
    }

    const qaBox = document.getElementById("prep-qa-list");
    if (qaBox) {
        qaBox.innerHTML = (report.interview_qas || [])
            .map(
                (qa) => `
            <div class="qa-item">
                <div class="qa-q">Q: ${escapeHtml(qa.question)}</div>
                <div class="qa-a">${escapeHtml(qa.key_talking_points)}</div>
            </div>
        `
            )
            .join("");
    }

    const slidesBox = document.getElementById("prep-slides-grid");
    if (slidesBox) {
        slidesBox.innerHTML = (report.presentation_slides || [])
            .map(
                (s) => `
            <div class="slide-card">
                <span class="slide-num">SLIDE 0${s.slide_number}</span>
                <h4 class="slide-title">${escapeHtml(s.title)}</h4>
                <div class="slide-sub">${escapeHtml(s.subtitle)}</div>
                <ul class="slide-bullets">
                    ${(s.bullet_points || []).map((b) => `<li>${escapeHtml(b)}</li>`).join("")}
                </ul>
                <div class="slide-notes"><strong>Speaker Note:</strong> ${escapeHtml(s.speaker_notes)}</div>
            </div>
        `
            )
            .join("");
    }
}

function copyPresentationMarkdown() {
    const md = document.getElementById("prep-markdown-raw")?.value || "";
    if (!md) {
        showToast("Generate a presentation deck first");
        return;
    }
    copyToClipboard(md, "Presentation Deck Markdown");
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function escapeQuotes(str) {
    if (!str) return "";
    return String(str).replace(/'/g, "\\'").replace(/"/g, "&quot;");
}
