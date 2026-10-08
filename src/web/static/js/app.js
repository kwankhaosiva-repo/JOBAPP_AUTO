/**
 * Job Application Workspace — Multi-Agent Semi-Auto Client Logic
 */

let candidateProfile = null;
let allHistoryRecords = [];
let currentStatusFilter = 'All';
let supportedPlatforms = [];
let lastPrepMarkdown = '';

document.addEventListener('DOMContentLoaded', async () => {
    await loadProfile();
    await loadPlatforms();
    await loadHistory();
    setupEventListeners();
});

// --- Profile Initialization ---

async function loadProfile() {
    try {
        const res = await fetch('/api/profile');
        if (res.ok) {
            candidateProfile = await res.json();
            document.getElementById('profile-name').textContent = candidateProfile.name;
            if (candidateProfile.resume_pdf_path) {
                document.getElementById('chip-pdf-path').title = candidateProfile.resume_pdf_path;
            }
        }
    } catch (e) {
        console.error('Error loading profile:', e);
    }
}

// --- Platforms & Search Dispatch ---

async function loadPlatforms() {
    try {
        const res = await fetch('/api/platforms');
        if (!res.ok) return;
        supportedPlatforms = await res.json();

        const grid = document.getElementById('platforms-grid');
        grid.innerHTML = '';

        supportedPlatforms.forEach(p => {
            const card = document.createElement('div');
            card.className = 'platform-card';

            card.innerHTML = `
                <div class="platform-top">
                    <div>
                        <div class="platform-name">${escapeHtml(p.name)}</div>
                        <span class="platform-tag">${escapeHtml(p.tag)}</span>
                    </div>
                    <span class="platform-dot" style="background-color: ${p.color || '#2563eb'};"></span>
                </div>
                <div class="platform-actions">
                    <button class="btn btn-secondary btn-sm" onclick="quickSearchPlatform('${p.id}')">
                        Search
                    </button>
                    <button class="btn btn-outline btn-sm" title="Copy Autofill Payload" onclick="copyPlatformPayload('${p.id}')">
                        Copy Info
                    </button>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (e) {
        console.error('Error loading platforms:', e);
    }
}

async function quickSearchPlatform(platformId) {
    const kw = document.getElementById('quick-keyword').value || 'AI Engineer';
    const loc = document.getElementById('quick-location').value || 'Bangkok';

    try {
        const res = await fetch('/api/platforms/search-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: platformId, keywords: kw, location: loc })
        });
        const data = await res.json();
        if (data.url) {
            window.open(data.url, '_blank');
            showToast(`Opened ${platformId.toUpperCase()} search for "${kw}"`);
        }
    } catch (e) {
        showToast('Failed to generate search link: ' + e.message, 'error');
    }
}

async function copyPlatformPayload(platformId) {
    const minSalary = parseInt(document.getElementById('input-min-salary').value) || 40000;
    const maxSalary = parseInt(document.getElementById('input-max-salary').value) || 45000;
    const coverLetter = document.getElementById('cover-letter-output').value || '';

    try {
        const res = await fetch('/api/autofill-payload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                platform_id: platformId,
                min_salary: minSalary,
                max_salary: maxSalary,
                cover_letter: coverLetter
            })
        });
        const payload = await res.json();
        const payloadSummary =
`Name: ${payload.candidate_name_en} (${payload.candidate_name_th})
Email: ${payload.email}
Phone: ${payload.phone}
Expected Salary: ${payload.expected_salary_text_en}
Resume Path: ${payload.resume_pdf_path}
Portfolio: ${payload.portfolio}
LinkedIn: ${payload.linkedin}
GitHub: ${payload.github}`;

        await navigator.clipboard.writeText(payloadSummary);
        showToast(`Copied profile & salary payload for ${payload.platform}`);
    } catch (e) {
        showToast('Error generating payload: ' + e.message, 'error');
    }
}

// --- Salary Controls ---

function handleSalaryChange() {
    const min = parseInt(document.getElementById('input-min-salary').value) || 40000;
    const max = parseInt(document.getElementById('input-max-salary').value) || 45000;
    const includeUnspecified = document.getElementById('include-unspecified-toggle').checked;

    document.getElementById('stat-salary-display').textContent = `${(min / 1000).toFixed(0)}k - ${(max / 1000).toFixed(0)}k`;
    const chipVal = document.getElementById('chip-salary-val');
    if (chipVal) {
        chipVal.textContent = `${min.toLocaleString()} - ${max.toLocaleString()} THB`;
    }
    document.getElementById('preview-salary-badge').textContent =
        `Form Salary Value: ${min.toLocaleString()} - ${max.toLocaleString()} THB (Negotiable)`;

    const statusBadge = document.getElementById('stat-strategy-status');
    if (statusBadge) {
        statusBadge.textContent = includeUnspecified ? 'Smart Auto' : 'Strict Tag';
    }
}

function setSalaryPreset(min, max, btnEl) {
    document.getElementById('input-min-salary').value = min;
    document.getElementById('input-max-salary').value = max;
    document.querySelectorAll('.btn-preset').forEach(b => b.classList.remove('active'));
    if (btnEl) {
        btnEl.classList.add('active');
    }
    handleSalaryChange();
    showToast(`Expected salary updated to ${min.toLocaleString()} - ${max.toLocaleString()} THB`);
}

// --- Multi-Agent Compatibility Evaluation & Auto-Shortlist ---

async function evaluateJobCompatibility(autoShortlist = false) {
    const company = document.getElementById('app-company').value.trim();
    const position = document.getElementById('app-position').value.trim();
    const jd = document.getElementById('app-jd').value.trim();
    const link = document.getElementById('app-link').value.trim();
    const platform = document.getElementById('app-platform').value;
    const industry = document.getElementById('app-industry').value.trim();
    const priority = document.getElementById('app-priority').value;
    const min = parseInt(document.getElementById('input-min-salary').value) || 40000;
    const max = parseInt(document.getElementById('input-max-salary').value) || 45000;
    const provider = document.getElementById('llm-provider-select').value;

    if (!company || !position) {
        showToast('Please enter Company Name and Job Position first.', 'error');
        return;
    }

    try {
        const res = await fetch('/api/pipeline/shortlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: company,
                job_position: position,
                job_description: jd,
                link: link,
                platform: platform,
                industry: industry,
                priority: priority,
                min_salary: min,
                max_salary: max,
                auto_save_if_compatible: autoShortlist,
                force_save: false,
                llm_provider: provider
            })
        });

        if (!res.ok) {
            showToast('Failed to run compatibility pipeline', 'error');
            return;
        }

        const data = await res.json();
        const ev = data.evaluation;

        // Render Compatibility Report
        const card = document.getElementById('compat-report-card');
        const verdictEl = document.getElementById('compat-verdict-label');
        const engineEl = document.getElementById('compat-engine-tag');
        const overallEl = document.getElementById('compat-overall-score');
        const skillEl = document.getElementById('compat-skill-score');
        const goalEl = document.getElementById('compat-goal-score');
        const salEl = document.getElementById('compat-salary-score');
        const reasonEl = document.getElementById('compat-reasoning');
        const skillsRow = document.getElementById('compat-skills-row');

        let accentColor = '#2563eb';
        if (ev.overall_score >= 80) accentColor = '#10b981';
        else if (ev.overall_score >= 65) accentColor = '#f59e0b';
        else accentColor = '#ef4444';

        card.style.borderLeftColor = accentColor;
        verdictEl.textContent = ev.verdict_label;
        engineEl.textContent = ev.engine_used;
        overallEl.textContent = `${ev.overall_score}%`;
        overallEl.style.color = accentColor;
        skillEl.textContent = `${ev.skill_match_score}%`;
        goalEl.textContent = `${ev.goal_alignment_score}%`;
        salEl.textContent = `${ev.salary_fit_score}%`;
        reasonEl.textContent = ev.reasoning;

        // Render matched & growth skills badges
        skillsRow.innerHTML = '';
        if ((ev.matched_skills && ev.matched_skills.length > 0) || (ev.growth_skills && ev.growth_skills.length > 0)) {
            skillsRow.style.display = 'flex';
            (ev.matched_skills || []).forEach(s => {
                const span = document.createElement('span');
                span.className = 'skill-badge';
                span.textContent = `Match: ${s}`;
                skillsRow.appendChild(span);
            });
            (ev.growth_skills || []).forEach(g => {
                const span = document.createElement('span');
                span.className = 'skill-badge growth';
                span.textContent = `Growth: ${g}`;
                skillsRow.appendChild(span);
            });
        } else {
            skillsRow.style.display = 'none';
        }

        // Update domain dropdown and cover letter
        if (ev.suggested_domain) {
            document.getElementById('app-focus-domain').value = ev.suggested_domain;
        }
        const output = document.getElementById('cover-letter-output');
        output.value = data.cover_letter;
        updateLetterStats(data.cover_letter);

        if (data.saved_to_history) {
            showToast(`Compatible (${ev.overall_score}%)! Shortlisted "${company}" as 'Considering' in CSV & Excel.`);
            await loadHistory();
        } else if (autoShortlist && !ev.is_compatible) {
            showToast(`Score ${ev.overall_score}% is below auto-shortlist threshold (65%). Click 'Save Directly' if you still want it.`, 'error');
        } else {
            showToast(`Evaluated ${company}: ${ev.overall_score}% compatibility`);
        }
    } catch (e) {
        showToast('Error running compatibility evaluation: ' + e.message, 'error');
    }
}

function onPlatformSelectChange() {
    const platId = document.getElementById('app-platform').value;
    const guideTitle = document.getElementById('guide-title');
    const guideText = document.getElementById('guide-text');

    const plat = supportedPlatforms.find(p => p.id === platId);
    if (plat) {
        guideTitle.textContent = `${plat.name} Tip:`;
        guideText.textContent = plat.instructions.split('\n')[0];
    }
}

function updateLetterStats(text) {
    if (!text) {
        document.getElementById('letter-word-count').textContent = '0 words';
        document.getElementById('letter-read-time').textContent = '0 min read';
        return;
    }
    const words = text.trim().split(/\s+/).length;
    const readTime = Math.ceil(words / 200);
    document.getElementById('letter-word-count').textContent = `${words} words`;
    document.getElementById('letter-read-time').textContent = `${readTime} min read`;
}

async function copyCoverLetter() {
    const text = document.getElementById('cover-letter-output').value.trim();
    if (!text) {
        showToast('Generate or evaluate a job first before copying.', 'error');
        return;
    }
    await navigator.clipboard.writeText(text);
    showToast('Cover letter copied to clipboard');
}

async function submitApplication() {
    const company = document.getElementById('app-company').value.trim();
    const position = document.getElementById('app-position').value.trim();
    const link = document.getElementById('app-link').value.trim();
    const location = document.getElementById('app-location').value.trim();
    const industry = document.getElementById('app-industry').value.trim();
    const priority = document.getElementById('app-priority').value;
    const status = document.getElementById('app-status').value;
    const jd = document.getElementById('app-jd').value.trim();
    const coverLetter = document.getElementById('cover-letter-output').value.trim();
    const min = parseInt(document.getElementById('input-min-salary').value) || 40000;
    const max = parseInt(document.getElementById('input-max-salary').value) || 45000;

    if (!company || !position) {
        showToast('Company Name and Job Position are required.', 'error');
        return;
    }

    const newRecord = {
        company: company,
        job_position: position,
        link: link,
        location: location || 'Bangkok, Thailand',
        industry: industry,
        priority: priority,
        status: status,
        salary: `${min.toLocaleString()} - ${max.toLocaleString()} THB`,
        jd: jd,
        job_letter: coverLetter,
        notes: `Platform: ${document.getElementById('app-platform').value}`
    };

    try {
        const res = await fetch('/api/history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newRecord)
        });

        if (res.ok) {
            showToast(`Saved "${company}" (${status}) to CSV & Excel`);
            await loadHistory();
            document.getElementById('app-company').value = '';
            document.getElementById('app-position').value = '';
            document.getElementById('app-link').value = '';
            document.getElementById('app-jd').value = '';
        } else {
            const err = await res.json();
            showToast('Error saving application: ' + (err.detail || 'Failed'), 'error');
        }
    } catch (e) {
        showToast('Failed to save application: ' + e.message, 'error');
    }
}

// --- History Table & Semi-Auto Workflow ---

async function loadHistory() {
    try {
        const res = await fetch('/api/history');
        if (!res.ok) return;
        const data = await res.json();
        allHistoryRecords = data.records;

        const stats = data.stats;
        document.getElementById('stat-total-apps').textContent = stats.total_applications;
        document.getElementById('stat-considering-apps').textContent = stats.considering_count || 0;
        document.getElementById('stat-sent-apps').textContent = stats.resumes_sent;

        document.getElementById('count-all').textContent = stats.total_applications;
        document.getElementById('count-considering').textContent = stats.considering_count || 0;
        document.getElementById('count-sent').textContent = stats.resumes_sent;
        document.getElementById('count-notpass').textContent = stats.not_pass;
        document.getElementById('count-interview').textContent = stats.interviewing;

        renderHistoryTable();
        populatePrepSelect();
    } catch (e) {
        console.error('Error loading history:', e);
    }
}

function setStatusFilter(status) {
    currentStatusFilter = status;
    document.querySelectorAll('#status-filter-tabs .tab-item').forEach(btn => {
        const isMatch =
            (status === 'All' && btn.textContent.startsWith('All')) ||
            (status === 'Considering' && btn.textContent.startsWith('Considering')) ||
            (status === 'Submitted' && btn.textContent.startsWith('Submitted')) ||
            (status === 'Interview Scheduled' && btn.textContent.startsWith('Interview')) ||
            (status === 'Not Pass?' && btn.textContent.startsWith('Closed'));
        btn.classList.toggle('active', isMatch);
    });
    renderHistoryTable();
}

function filterHistoryTable() {
    renderHistoryTable();
}

function renderHistoryTable() {
    const searchTerm = (document.getElementById('history-search').value || '').toLowerCase();
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '';

    const filtered = allHistoryRecords.filter(r => {
        let matchesStatus = true;
        if (currentStatusFilter === 'Submitted') {
            matchesStatus = r.status === 'Submitted' || r.status === 'Resume Sent';
        } else if (currentStatusFilter !== 'All') {
            matchesStatus = r.status === currentStatusFilter;
        }
        const matchesSearch = !searchTerm ||
            r.company.toLowerCase().includes(searchTerm) ||
            r.job_position.toLowerCase().includes(searchTerm) ||
            r.notes.toLowerCase().includes(searchTerm);
        return matchesStatus && matchesSearch;
    });

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:28px; color:var(--text-dim);">No matching records in this queue.</td></tr>`;
        return;
    }

    filtered.forEach((r, idx) => {
        const tr = document.createElement('tr');

        let statusClass = 'status-sent';
        if (r.status === 'Considering') statusClass = 'status-considering';
        else if (r.status.includes('Interview') || r.status === 'HR Contacted') statusClass = 'status-interview';
        else if (r.status.includes('Not Pass')) statusClass = 'status-notpass';

        const hasLetter = r.job_letter && r.job_letter.trim().length > 10;
        const isConsidering = r.status === 'Considering';
        const isSubmittedOrActive = r.status === 'Submitted' || r.status === 'Resume Sent' || r.status.includes('Interview') || r.status === 'HR Contacted';

        tr.innerHTML = `
            <td class="mono" style="color:var(--text-dim);">${r.id || idx + 1}</td>
            <td>
                <div class="company-cell-name">${escapeHtml(r.company || 'Unnamed Company')}</div>
                ${r.industry ? `<div class="cell-sub">${escapeHtml(r.industry)}</div>` : ''}
            </td>
            <td>
                <div>${escapeHtml(r.job_position || '-')}</div>
                ${r.notes ? `<div class="cell-sub">${escapeHtml(r.notes)}</div>` : ''}
            </td>
            <td>
                <select class="status-select ${statusClass}" onchange="updateRowStatus(${r.id}, this.value)">
                    <option value="Considering" ${r.status === 'Considering' ? 'selected' : ''}>Considering</option>
                    <option value="Submitted" ${r.status === 'Submitted' ? 'selected' : ''}>Submitted</option>
                    <option value="Resume Sent" ${r.status === 'Resume Sent' ? 'selected' : ''}>Resume Sent</option>
                    <option value="HR Contacted" ${r.status === 'HR Contacted' ? 'selected' : ''}>HR Contacted</option>
                    <option value="Interview Scheduled" ${r.status === 'Interview Scheduled' ? 'selected' : ''}>Interview Scheduled</option>
                    <option value="Not Pass?" ${r.status === 'Not Pass?' ? 'selected' : ''}>Not Pass?</option>
                    <option value="Draft" ${r.status === 'Draft' ? 'selected' : ''}>Draft</option>
                </select>
            </td>
            <td class="mono" style="font-size:0.77rem; color:var(--text-muted);">${escapeHtml(r.resume_sent || (isConsidering ? 'Pending' : '-'))}</td>
            <td class="mono" style="font-size:0.77rem;">${escapeHtml(r.salary || r.offer_salary || '40,000 - 45,000 THB')}</td>
            <td style="text-align: right;">
                <div style="display:inline-flex; gap:5px; justify-content:flex-end; flex-wrap:wrap;">
                    ${isConsidering ? `
                        <button class="btn btn-emerald btn-sm" onclick="updateRowStatus(${r.id}, 'Submitted')" title="Mark as manually submitted">
                            Mark Submitted
                        </button>
                    ` : ''}
                    ${isSubmittedOrActive ? `
                        <button class="btn btn-secondary btn-sm" onclick="openPrepForRecord(${r.id})" title="Prepare Company Info & 5-Slide Presentation">
                            Prep Deck
                        </button>
                    ` : ''}
                    ${hasLetter ? `
                        <button class="btn btn-outline btn-sm" onclick="viewSavedLetter(${r.id})">
                            Letter
                        </button>
                    ` : ''}
                    ${r.link ? `
                        <a href="${escapeHtml(r.link)}" target="_blank" class="btn btn-outline btn-sm" title="Open Job Posting">
                            Link
                        </a>
                    ` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function updateRowStatus(recordId, newStatus) {
    try {
        const res = await fetch('/api/history/status', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ record_id: recordId, status: newStatus })
        });
        if (res.ok) {
            showToast(`Updated record #${recordId} status to "${newStatus}" (CSV & Excel synced)`);
            await loadHistory();
            if (newStatus === 'Submitted') {
                openPrepForRecord(recordId);
            }
        } else {
            showToast('Failed to update status', 'error');
        }
    } catch (e) {
        showToast('Error updating status: ' + e.message, 'error');
    }
}

// --- Section 5: Company Intelligence & Presentation Prep Mode ---

function populatePrepSelect() {
    const sel = document.getElementById('prep-job-select');
    if (!sel) return;
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">-- Select a Submitted / Active Application --</option>';

    // Prioritize Submitted, Resume Sent, Interview Scheduled, then others
    const eligible = allHistoryRecords.filter(r => r.company && r.company.trim() !== '');
    eligible.forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.id;
        opt.textContent = `#${r.id} [${r.status}] ${r.company} — ${r.job_position}`;
        sel.appendChild(opt);
    });

    if (currentVal) {
        sel.value = currentVal;
    }
}

function onPrepSelectChange() {
    const val = document.getElementById('prep-job-select').value;
    if (val) {
        generatePrepForRecordId(parseInt(val));
    }
}

function generatePrepFromSelected() {
    const val = document.getElementById('prep-job-select').value;
    if (val) {
        generatePrepForRecordId(parseInt(val));
    } else if (allHistoryRecords.length > 0) {
        // Default to first Submitted / Resume Sent record
        const sub = allHistoryRecords.find(r => r.status === 'Submitted' || r.status === 'Resume Sent') || allHistoryRecords[0];
        document.getElementById('prep-job-select').value = sub.id;
        generatePrepForRecordId(sub.id);
    }
}

function openPrepForRecord(recordId) {
    const sel = document.getElementById('prep-job-select');
    if (sel) {
        sel.value = recordId;
    }
    const section = document.getElementById('prep-studio-section');
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    generatePrepForRecordId(recordId);
}

async function generatePrepForRecordId(recordId) {
    const rec = allHistoryRecords.find(r => r.id === recordId);
    if (!rec) return;

    try {
        const res = await fetch('/api/prep/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                record_id: rec.id,
                company_name: rec.company,
                job_position: rec.job_position,
                industry: rec.industry || '',
                job_description: rec.jd || ''
            })
        });
        if (!res.ok) {
            showToast('Failed to generate presentation prep report', 'error');
            return;
        }
        const report = await res.json();
        lastPrepMarkdown = report.markdown_deck;
        renderPrepReport(report);
        showToast(`Prepared 5-slide presentation & company brief for ${report.company_name}`);
    } catch (e) {
        showToast('Error generating prep report: ' + e.message, 'error');
    }
}

function renderPrepReport(report) {
    const container = document.getElementById('prep-content-area');

    const linksHtml = (report.research_links || []).map(l => `
        <a href="${escapeHtml(l.url)}" target="_blank" class="research-link-item">
            <span>${escapeHtml(l.label)}</span>
            <span class="mono" style="font-size:0.72rem; color:#60a5fa;">Open &rarr;</span>
        </a>
    `).join('');

    const qasHtml = (report.interview_qas || []).map(qa => `
        <div class="qa-item">
            <div class="qa-q">${escapeHtml(qa.question)}</div>
            <div class="qa-a">${escapeHtml(qa.key_talking_points)}</div>
        </div>
    `).join('');

    const slidesHtml = (report.presentation_slides || []).map(s => {
        const bullets = (s.bullet_points || []).map(b => `<li>${escapeHtml(b)}</li>`).join('');
        return `
            <div class="slide-card">
                <div class="slide-header">
                    <span class="slide-title">${escapeHtml(s.title)}</span>
                    <span class="slide-num mono">Slide ${s.slide_number} / 5</span>
                </div>
                <div class="slide-subtitle">${escapeHtml(s.subtitle)}</div>
                <ul class="slide-bullets">${bullets}</ul>
                <div class="slide-notes">
                    <strong>Speaker Note:</strong> ${escapeHtml(s.speaker_notes)}
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = `
        <div class="prep-layout">
            <div class="prep-intel-column">
                <div class="prep-box">
                    <div class="prep-box-title">
                        <span>Company Intelligence</span>
                        <span class="prep-category-badge">${escapeHtml(report.industry_category)}</span>
                    </div>
                    <p class="prep-text">${escapeHtml(report.company_overview)}</p>
                    <p class="prep-text" style="color:var(--text-muted);">
                        <strong>Key Technical &amp; Business Focus:</strong> ${escapeHtml(report.strategic_alignment)}
                    </p>
                </div>

                <div class="prep-box">
                    <div class="prep-box-title">
                        <span>Deep-Dive Research Links</span>
                    </div>
                    <div class="research-link-list">
                        ${linksHtml}
                    </div>
                </div>

                <div class="prep-box">
                    <div class="prep-box-title">
                        <span>Targeted Interview Q&amp;A Strategy</span>
                    </div>
                    ${qasHtml}
                </div>
            </div>

            <div class="slides-column">
                <div class="slides-grid">
                    ${slidesHtml}
                </div>
            </div>
        </div>
    `;
}

async function copyPrepMarkdown() {
    if (!lastPrepMarkdown) {
        showToast('Select a submitted job and generate a presentation kit first.', 'error');
        return;
    }
    await navigator.clipboard.writeText(lastPrepMarkdown);
    showToast('Copied 5-slide Markdown presentation deck to clipboard');
}

// --- Modal & Quick Copy Helpers ---

function viewSavedLetter(recordId) {
    const record = allHistoryRecords.find(r => r.id === recordId);
    if (!record || !record.job_letter) return;

    document.getElementById('modal-company-title').textContent = record.company;
    document.getElementById('modal-position-title').textContent = record.job_position;
    document.getElementById('modal-letter-content').value = record.job_letter;
    document.getElementById('letter-modal').style.display = 'flex';
}

function closeLetterModal() {
    document.getElementById('letter-modal').style.display = 'none';
}

function closeModalOnOverlay(e) {
    if (e.target.id === 'letter-modal') {
        closeLetterModal();
    }
}

async function copyModalLetter() {
    const text = document.getElementById('modal-letter-content').value;
    await navigator.clipboard.writeText(text);
    showToast('Cover letter copied to clipboard');
}

async function copySnippet(text, label) {
    await navigator.clipboard.writeText(text);
    showToast(`Copied ${label}`);
}

async function copySalaryText() {
    const min = parseInt(document.getElementById('input-min-salary').value) || 40000;
    const max = parseInt(document.getElementById('input-max-salary').value) || 45000;
    const text = `${min.toLocaleString()} - ${max.toLocaleString()} THB (Negotiable)`;
    await navigator.clipboard.writeText(text);
    showToast(`Copied Expected Salary: ${text}`);
}

async function copyResumePath() {
    if (candidateProfile && candidateProfile.resume_pdf_path) {
        await navigator.clipboard.writeText(candidateProfile.resume_pdf_path);
        showToast('Copied Resume PDF file path');
    }
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = type === 'error' ? 'toast toast-error' : 'toast';
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(6px)';
        setTimeout(() => toast.remove(), 200);
    }, 2800);
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function setupEventListeners() {
    const letterArea = document.getElementById('cover-letter-output');
    if (letterArea) {
        letterArea.addEventListener('input', (e) => {
            updateLetterStats(e.target.value);
        });
    }
}
