// ============================================================================
// Docling Parser - Main Application JavaScript
// ============================================================================

// Configuration
const API_BASE_URL = 'http://localhost:8000';
const POLL_INTERVAL = 2000; // Poll every 2 seconds

// State
let activePolling = new Set();
let allJobs = [];

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    checkAPIHealth();
    loadJobs();
});

function initializeApp() {
    // Show/hide description options based on checkbox
    const describeImagesCheckbox = document.getElementById('describeImages');
    const descriptionOptionsGroup = document.getElementById('descriptionOptionsGroup');

    describeImagesCheckbox.addEventListener('change', (e) => {
        descriptionOptionsGroup.style.display = e.target.checked ? 'block' : 'none';
        if (e.target.checked) {
            document.getElementById('descriptionProvider').value = 'docling';
        } else {
            document.getElementById('descriptionProvider').value = 'none';
        }
    });
}

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // Upload form
    document.getElementById('uploadForm').addEventListener('submit', handleUpload);

    // Jobs refresh
    document.getElementById('refreshJobsBtn').addEventListener('click', loadJobs);

    // Status filter
    document.getElementById('statusFilter').addEventListener('change', filterJobs);

    // API Info
    document.getElementById('apiInfoLink').addEventListener('click', showAPIInfo);
    document.getElementById('closeApiInfo').addEventListener('click', hideAPIInfo);

    // Modal close
    document.getElementById('closeModal').addEventListener('click', closeJobModal);
}

// ============================================================================
// API Health Check
// ============================================================================

async function checkAPIHealth() {
    const statusElement = document.getElementById('apiStatus');

    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        if (data.status === 'healthy') {
            statusElement.className = 'alert alert-success';
            statusElement.innerHTML = `<span>API Connected - ${data.service} v${data.version}</span>`;
            setTimeout(() => statusElement.classList.add('hidden'), 3000);
        }
    } catch (error) {
        statusElement.className = 'alert alert-error';
        statusElement.innerHTML = `<span>API Connection Failed - Please ensure the API is running at ${API_BASE_URL}</span>`;
        statusElement.classList.remove('hidden');
    }
}

// ============================================================================
// Document Upload
// ============================================================================

async function handleUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        showAlert('Please select a file', 'error');
        return;
    }

    // Prepare form data
    const formData = new FormData();
    formData.append('file', file);

    // Get form values
    const parsingMode = document.getElementById('parsingMode').value;
    const extractImages = document.getElementById('extractImages').checked;
    const extractTables = document.getElementById('extractTables').checked;
    const imagesScale = document.getElementById('imageScale').value;
    const describeImages = document.getElementById('describeImages').checked;
    const descriptionProvider = document.getElementById('descriptionProvider').value;
    const descriptionPrompt = document.getElementById('descriptionPrompt').value;

    // Build URL with query parameters
    const params = new URLSearchParams({
        parsing_mode: parsingMode,
        extract_images: extractImages,
        extract_tables: extractTables,
        images_scale: imagesScale,
        describe_images: describeImages,
        description_provider: descriptionProvider
    });

    if (descriptionPrompt) {
        params.append('description_prompt', descriptionPrompt);
    }

    // Show progress
    showUploadProgress();

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/parse/document?${params}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = await response.json();

        // Hide progress
        hideUploadProgress();

        // Show success message
        showAlert(`Document uploaded successfully! Job ID: ${result.job_id}`, 'success');

        // Clear form
        document.getElementById('uploadForm').reset();

        // Reload jobs
        loadJobs();

        // Start polling for this job
        pollJobStatus(result.job_id);

    } catch (error) {
        hideUploadProgress();
        showAlert(`Upload failed: ${error.message}`, 'error');
    }
}

function showUploadProgress() {
    document.getElementById('uploadProgress').classList.remove('hidden');
    document.getElementById('uploadBtn').disabled = true;
    animateProgress();
}

function hideUploadProgress() {
    document.getElementById('uploadProgress').classList.add('hidden');
    document.getElementById('uploadBtn').disabled = false;
    document.getElementById('progressBar').style.width = '0%';
}

function animateProgress() {
    const progressBar = document.getElementById('progressBar');
    let width = 0;
    const interval = setInterval(() => {
        if (width >= 90) {
            clearInterval(interval);
        } else {
            width += 10;
            progressBar.style.width = width + '%';
        }
    }, 200);
}

// ============================================================================
// Jobs Management
// ============================================================================

async function loadJobs() {
    const jobsList = document.getElementById('jobsList');
    const loading = document.getElementById('jobsLoading');

    loading.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/jobs`);
        const data = await response.json();

        allJobs = data.jobs || [];
        displayJobs(allJobs);

        // Start polling for active jobs
        allJobs.forEach(job => {
            if (job.status === 'pending' || job.status === 'processing') {
                pollJobStatus(job.job_id);
            }
        });

    } catch (error) {
        jobsList.innerHTML = `
            <div class="alert alert-error">
                <span>Failed to load jobs: ${error.message}</span>
            </div>
        `;
    } finally {
        loading.classList.add('hidden');
    }
}

function displayJobs(jobs) {
    const jobsList = document.getElementById('jobsList');

    if (jobs.length === 0) {
        jobsList.innerHTML = `
            <div class="text-center text-muted">
                <p>No jobs found. Upload a document to get started.</p>
            </div>
        `;
        return;
    }

    // Sort by created_at descending
    jobs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

    jobsList.innerHTML = jobs.map(job => createJobCard(job)).join('');

    // Attach event listeners
    jobs.forEach(job => {
        const statusBtn = document.getElementById(`status-${job.job_id}`);
        const resultsBtn = document.getElementById(`results-${job.job_id}`);

        if (statusBtn) {
            statusBtn.addEventListener('click', () => showJobStatus(job.job_id));
        }

        if (resultsBtn) {
            resultsBtn.addEventListener('click', () => {
                window.location.href = `results.html?job_id=${job.job_id}`;
            });
        }
    });
}

function createJobCard(job) {
    const createdDate = new Date(job.created_at).toLocaleString();
    const statusClass = `status-${job.status}`;

    return `
        <div class="job-item">
            <div class="job-info">
                <div class="job-id">Job ID: ${job.job_id}</div>
                <div class="job-filename">${job.filename || 'Unknown'}</div>
                <div class="job-meta">
                    <span>Created: ${createdDate}</span> |
                    <span>Mode: ${job.parsing_mode || 'standard'}</span>
                </div>
            </div>
            <div class="job-actions">
                <span class="status-badge ${statusClass}">${job.status}</span>
                <button class="btn btn-secondary btn-small" id="status-${job.job_id}">
                    Status
                </button>
                ${job.status === 'completed' ? `
                    <button class="btn btn-primary btn-small" id="results-${job.job_id}">
                        View Results
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

function filterJobs() {
    const filterValue = document.getElementById('statusFilter').value;

    if (!filterValue) {
        displayJobs(allJobs);
        return;
    }

    const filtered = allJobs.filter(job => job.status === filterValue);
    displayJobs(filtered);
}

// ============================================================================
// Job Status Polling
// ============================================================================

async function pollJobStatus(jobId) {
    if (activePolling.has(jobId)) {
        return; // Already polling this job
    }

    activePolling.add(jobId);

    const poll = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/parse/jobs/${jobId}`);
            const job = await response.json();

            // Update job in list if displayed
            updateJobInList(job);

            // Stop polling if job is completed or failed
            if (job.status === 'completed' || job.status === 'failed') {
                activePolling.delete(jobId);

                if (job.status === 'completed') {
                    showAlert(`Job ${jobId} completed successfully!`, 'success');
                } else {
                    showAlert(`Job ${jobId} failed: ${job.error_message}`, 'error');
                }

                return;
            }

            // Continue polling
            setTimeout(poll, POLL_INTERVAL);

        } catch (error) {
            console.error('Polling error:', error);
            activePolling.delete(jobId);
        }
    };

    poll();
}

function updateJobInList(updatedJob) {
    const index = allJobs.findIndex(j => j.job_id === updatedJob.job_id);
    if (index !== -1) {
        allJobs[index] = updatedJob;
        displayJobs(allJobs);
    }
}

// ============================================================================
// Job Status Modal
// ============================================================================

async function showJobStatus(jobId) {
    const modal = document.getElementById('jobStatusModal');
    const content = document.getElementById('jobStatusContent');

    modal.classList.remove('hidden');
    content.innerHTML = '<div class="spinner"></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/parse/jobs/${jobId}`);
        const job = await response.json();

        content.innerHTML = `
            <div class="form-group">
                <label>Job ID</label>
                <div class="job-id">${job.job_id}</div>
            </div>

            <div class="form-group">
                <label>Status</label>
                <span class="status-badge status-${job.status}">${job.status}</span>
            </div>

            ${job.progress_percent !== null ? `
                <div class="form-group">
                    <label>Progress</label>
                    <div class="progress-container">
                        <div class="progress-bar" style="width: ${job.progress_percent}%"></div>
                    </div>
                    <div class="text-center mt-1">${job.progress_percent}%</div>
                </div>
            ` : ''}

            <div class="form-group">
                <label>Created At</label>
                <div>${new Date(job.created_at).toLocaleString()}</div>
            </div>

            ${job.completed_at ? `
                <div class="form-group">
                    <label>Completed At</label>
                    <div>${new Date(job.completed_at).toLocaleString()}</div>
                </div>
            ` : ''}

            ${job.error_message ? `
                <div class="alert alert-error mt-2">
                    <span>${job.error_message}</span>
                </div>
            ` : ''}

            ${job.status === 'completed' ? `
                <div class="mt-3">
                    <a href="results.html?job_id=${job.job_id}" class="btn btn-primary">
                        View Results
                    </a>
                </div>
            ` : ''}
        `;

    } catch (error) {
        content.innerHTML = `
            <div class="alert alert-error">
                <span>Failed to load job status: ${error.message}</span>
            </div>
        `;
    }
}

function closeJobModal() {
    document.getElementById('jobStatusModal').classList.add('hidden');
}

// ============================================================================
// API Info
// ============================================================================

async function showAPIInfo() {
    const card = document.getElementById('apiInfoCard');
    const content = document.getElementById('apiInfoContent');

    card.classList.remove('hidden');
    content.innerHTML = '<div class="spinner"></div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/info`);
        const info = await response.json();

        content.innerHTML = `
            <div class="form-group">
                <label>API Version</label>
                <div>${info.api_version}</div>
            </div>

            <div class="form-group">
                <label>Supported File Extensions</label>
                <div class="flex gap-1" style="flex-wrap: wrap;">
                    ${info.supported_extensions.map(ext =>
                        `<span class="status-badge status-completed">${ext}</span>`
                    ).join('')}
                </div>
            </div>

            <div class="form-group">
                <label>Parsing Modes</label>
                <div class="flex gap-1" style="flex-wrap: wrap;">
                    ${info.parsing_modes.map(mode =>
                        `<span class="status-badge status-processing">${mode}</span>`
                    ).join('')}
                </div>
            </div>

            <div class="form-group">
                <label>Configuration Limits</label>
                <ul style="margin-left: 1.5rem;">
                    <li>Max File Size: ${info.limits.max_file_size_mb} MB</li>
                    <li>Result TTL: ${info.limits.result_ttl_seconds} seconds</li>
                    <li>Job Timeout: ${info.limits.job_timeout_seconds} seconds</li>
                </ul>
            </div>
        `;

    } catch (error) {
        content.innerHTML = `
            <div class="alert alert-error">
                <span>Failed to load API info: ${error.message}</span>
            </div>
        `;
    }
}

function hideAPIInfo() {
    document.getElementById('apiInfoCard').classList.add('hidden');
}

// ============================================================================
// Utility Functions
// ============================================================================

function showAlert(message, type = 'info') {
    const alertClass = `alert-${type}`;
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass}`;
    alert.innerHTML = `<span>${message}</span>`;

    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);

    setTimeout(() => {
        alert.remove();
    }, 5000);
}
