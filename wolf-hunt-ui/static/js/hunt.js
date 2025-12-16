class WolfHunt {
    constructor() {
        this.jobs = [];
        this.selectedJobs = new Set();
        this.activeSearches = 0;

        this.config = {
            apiBase: `http://${window.location.hostname}:5000`,
            boards: {
                ziprecruiter: { port: 5001, name: 'ZipRecruiter' },
                indeed: { port: 5004, name: 'Indeed' },
                remotive: { port: 5006, name: 'Remotive' },
                'graphql-jobs': { port: 5005, name: 'GraphQL Jobs' },
                gamebrain: { port: 5002, name: 'GameBrain' },
                'fantastic-jobs': { port: 5003, name: 'Fantastic Jobs' },
                whatjobs: { port: 5007, name: 'WhatJobs' }
            }
        };

        this.init();
    }

    init() {
        // Search button
        document.getElementById('search-btn').addEventListener('click', () => this.search());

        // Candidate filter
        document.getElementById('candidate-filter').addEventListener('change', () => this.filterByCandidate());

        // Enter key on search inputs
        document.getElementById('search-query').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.search();
        });
        document.getElementById('search-location').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.search();
        });

        // Resume generator
        document.getElementById('generate-resume').addEventListener('click', () => this.generateResume());

        // Bulk apply
        document.getElementById('bulk-apply').addEventListener('click', () => this.bulkApply());

        // View tracker
        document.getElementById('view-tracker').addEventListener('click', () => this.viewTracker());

        // Campaign launch
        document.getElementById('launch-campaign').addEventListener('click', () => this.launchCampaign());

        // Export CSV
        document.getElementById('export-csv').addEventListener('click', () => this.exportCSV());

        // Sort
        document.getElementById('sort-by').addEventListener('change', (e) => this.sortResults(e.target.value));

        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('job-modal').addEventListener('click', (e) => {
            if (e.target.id === 'job-modal') this.closeModal();
        });

        // Load stored jobs from database on page load
        this.loadStoredJobs();
    }

    async loadStoredJobs() {
        try {
            const candidate = document.getElementById('candidate-filter')?.value || '';
            const url = candidate
                ? `${this.config.apiBase}/api/jobs/scraped?candidate=${encodeURIComponent(candidate)}`
                : `${this.config.apiBase}/api/jobs/scraped`;

            const response = await fetch(url);
            const data = await response.json();

            if (data.success && data.jobs) {
                // Transform scraped jobs to match expected format
                this.jobs = data.jobs.map(job => ({
                    id: job.id,
                    title: job.title,
                    company: job.company,
                    location: job.location,
                    description: job.description,
                    url: job.url,
                    source: job.source,
                    board: job.board,
                    date: job.scraped_at || new Date().toISOString(),
                    candidate_match: job.candidate_match
                }));
                this.renderResults();
                this.updateStats();
                console.log(`[WOLF-HUNT] Loaded ${data.count} jobs from database`);
            }
        } catch (error) {
            console.error('[WOLF-HUNT] Failed to load stored jobs:', error);
        }
    }

    filterByCandidate() {
        this.loadStoredJobs();
    }

    async search() {
        const query = document.getElementById('search-query').value;
        const location = document.getElementById('search-location').value;

        if (!query.trim()) {
            alert('Enter a job title or keywords');
            return;
        }

        // Get selected boards
        const selectedBoards = Array.from(document.querySelectorAll('.board-toggle:checked'))
            .map(cb => cb.dataset.board);

        if (selectedBoards.length === 0) {
            alert('Select at least one job board');
            return;
        }

        // Clear previous results
        this.jobs = [];
        this.renderResults();
        this.showLoading();

        // Search all selected boards
        const promises = selectedBoards.map(board => this.searchBoard(board, query, location));

        this.activeSearches = promises.length;
        this.updateStats();

        const results = await Promise.allSettled(promises);

        results.forEach((result, index) => {
            if (result.status === 'fulfilled') {
                this.jobs.push(...result.value);
            } else {
                console.error(`Search failed for ${selectedBoards[index]}:`, result.reason);
            }
        });

        this.activeSearches = 0;
        this.updateStats();
        this.renderResults();
    }

    async searchBoard(board, query, location) {
        // Mock API call - replace with actual MCP server calls
        return new Promise((resolve, reject) => {
            setTimeout(() => {
                const mockJobs = this.generateMockJobs(board, query, location, 5);
                resolve(mockJobs);
            }, 1000 + Math.random() * 1000);
        });

        /* Real implementation would look like:
        try {
            const response = await fetch(`${this.config.apiBase}/mcp/${board}/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, location })
            });
            const data = await response.json();
            return data.jobs.map(job => ({
                ...job,
                source: this.config.boards[board].name,
                board: board
            }));
        } catch (error) {
            console.error(`Search error for ${board}:`, error);
            return [];
        }
        */
    }

    generateMockJobs(board, query, location, count) {
        const jobs = [];
        const companies = ['TechCorp', 'DataSystems', 'CloudNet', 'DevWorks', 'CodeFactory'];
        const titles = [query, `Senior ${query}`, `Lead ${query}`, `${query} Developer`];

        for (let i = 0; i < count; i++) {
            jobs.push({
                id: `${board}-${Date.now()}-${i}`,
                title: titles[Math.floor(Math.random() * titles.length)],
                company: companies[Math.floor(Math.random() * companies.length)],
                location: location === 'remote' ? 'Remote' : location,
                description: `Looking for a talented ${query} to join our team...`,
                source: this.config.boards[board].name,
                board: board,
                date: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
                url: `https://example.com/job/${board}-${i}`
            });
        }

        return jobs;
    }

    showLoading() {
        const container = document.getElementById('results-container');
        container.innerHTML = '<div class="loading">Hunting across job boards</div>';
    }

    renderResults() {
        const container = document.getElementById('results-container');

        if (this.jobs.length === 0) {
            container.innerHTML = '<div class="empty-state"><p>No jobs found. Try different keywords.</p></div>';
            return;
        }

        container.innerHTML = this.jobs.map(job => `
            <div class="job-card" data-job-id="${job.id}">
                <input type="checkbox" class="job-select" data-job-id="${job.id}">
                <div class="job-title">${job.title}</div>
                <div class="job-company">${job.company}</div>
                <div class="job-location">${job.location}</div>
                ${job.candidate_match ? `<span class="job-candidate">${job.candidate_match}</span>` : ''}
                <span class="job-source">${job.source}</span>
            </div>
        `).join('');

        // Add event listeners
        document.querySelectorAll('.job-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.classList.contains('job-select')) {
                    this.showJobDetail(card.dataset.jobId);
                }
            });
        });

        document.querySelectorAll('.job-select').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                e.stopPropagation();
                this.toggleJobSelection(e.target.dataset.jobId, e.target.checked);
            });
        });
    }

    toggleJobSelection(jobId, selected) {
        if (selected) {
            this.selectedJobs.add(jobId);
        } else {
            this.selectedJobs.delete(jobId);
        }

        const card = document.querySelector(`.job-card[data-job-id="${jobId}"]`);
        if (card) {
            card.classList.toggle('selected', selected);
        }

        document.getElementById('selected-count').textContent = this.selectedJobs.size;
        document.getElementById('bulk-apply').disabled = this.selectedJobs.size === 0;
    }

    showJobDetail(jobId) {
        const job = this.jobs.find(j => j.id === jobId);
        if (!job) return;

        const modal = document.getElementById('job-modal');
        const detail = document.getElementById('job-detail');

        detail.innerHTML = `
            <h2>${job.title}</h2>
            <h3>${job.company}</h3>
            <p><strong>Location:</strong> ${job.location}</p>
            <p><strong>Source:</strong> ${job.source}</p>
            <p><strong>Posted:</strong> ${new Date(job.date).toLocaleDateString()}</p>
            <hr style="margin: 20px 0; border-color: #333;">
            <p>${job.description}</p>
            <hr style="margin: 20px 0; border-color: #333;">
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn-primary" onclick="window.open('${job.url}', '_blank')">Apply on ${job.source}</button>
                <button class="btn-secondary" onclick="wolfHunt.generateResume('${job.title}')">Generate Resume</button>
                <button class="btn-secondary" onclick="wolfHunt.trackApplication('${job.id}')">Track Application</button>
            </div>
        `;

        modal.classList.remove('hidden');
        modal.classList.add('visible');
    }

    closeModal() {
        const modal = document.getElementById('job-modal');
        modal.classList.remove('visible');
        modal.classList.add('hidden');
    }

    async generateResume(jobTitle) {
        const title = jobTitle || document.getElementById('resume-job-title').value;
        if (!title) {
            alert('Enter a target job title');
            return;
        }

        alert(`Generating ATS-optimized resume for: ${title}\n\nThis will call the resume generator MCP...`);

        // TODO: Call resume generator MCP
        // await fetch(`${this.config.apiBase}/resume/generate`, {
        //     method: 'POST',
        //     body: JSON.stringify({ jobTitle: title })
        // });
    }

    async bulkApply() {
        if (this.selectedJobs.size === 0) return;

        const confirmed = confirm(`Apply to ${this.selectedJobs.size} selected jobs?`);
        if (!confirmed) return;

        alert(`Launching bulk apply for ${this.selectedJobs.size} jobs...\n\nThis will:\n- Generate custom resumes\n- Track applications\n- Queue follow-ups`);

        // TODO: Implement bulk apply logic
    }

    viewTracker() {
        alert('Application Tracker\n\nThis will open the tracking dashboard showing:\n- All applications\n- Response rates\n- Follow-up schedule\n- Interview pipeline');

        // TODO: Open tracker UI
    }

    launchCampaign() {
        alert('Launch Campaign\n\nThis will start:\n- Voice agent calls\n- Email follow-ups\n- LinkedIn outreach\n\nStatus will update in sidebar.');

        // TODO: Start campaign services
    }

    exportCSV() {
        if (this.jobs.length === 0) {
            alert('No jobs to export');
            return;
        }

        const csv = this.jobsToCSV();
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `wolf-hunt-${Date.now()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }

    jobsToCSV() {
        const headers = ['Title', 'Company', 'Location', 'Source', 'Date', 'URL'];
        const rows = this.jobs.map(job => [
            job.title,
            job.company,
            job.location,
            job.source,
            new Date(job.date).toLocaleDateString(),
            job.url
        ]);

        return [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');
    }

    sortResults(sortBy) {
        switch(sortBy) {
            case 'date':
                this.jobs.sort((a, b) => new Date(b.date) - new Date(a.date));
                break;
            case 'source':
                this.jobs.sort((a, b) => a.source.localeCompare(b.source));
                break;
            case 'title':
                this.jobs.sort((a, b) => a.title.localeCompare(b.title));
                break;
        }
        this.renderResults();
    }

    updateStats() {
        document.getElementById('jobs-count').textContent = this.jobs.length;
        document.getElementById('active-searches').textContent = this.activeSearches;
        // Applied count would come from tracker database
        document.getElementById('applied-count').textContent = '0';
    }

    trackApplication(jobId) {
        const job = this.jobs.find(j => j.id === jobId);
        if (!job) return;

        alert(`Tracking application for:\n${job.title} at ${job.company}\n\nThis will add to PostgreSQL tracker.`);

        // TODO: Save to tracking database
        this.closeModal();
    }
}

// Initialize on load
let wolfHunt;
document.addEventListener('DOMContentLoaded', () => {
    wolfHunt = new WolfHunt();
});
