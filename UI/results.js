// ============================================================================
// Docling Parser - Results Viewer JavaScript
// ============================================================================

// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentJobId = null;
let currentResults = null;
let currentTexts = [];
let currentTables = [];

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initializeResultsPage();
});

function initializeResultsPage() {
    // Get job ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    currentJobId = urlParams.get('job_id');

    if (!currentJobId) {
        showError('No job ID provided. Please select a job from the main page.');
        return;
    }

    // Update job ID display
    document.getElementById('jobIdDisplay').textContent = `Job ID: ${currentJobId}`;

    // Setup event listeners
    setupEventListeners();

    // Load results
    loadResults();
}

// ============================================================================
// Event Listeners
// ============================================================================

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            switchTab(e.target.dataset.tab);
        });
    });

    // Export buttons
    document.getElementById('exportMarkdown').addEventListener('click', exportMarkdown);
    document.getElementById('exportJSON').addEventListener('click', exportJSON);

    // Text filters
    document.getElementById('applyTextFilters').addEventListener('click', applyTextFilters);

    // Table format change
    document.getElementById('tableFormat').addEventListener('change', (e) => {
        loadTables(e.target.value);
    });
}

// ============================================================================
// Tab Management
// ============================================================================

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
}

// ============================================================================
// Load Results
// ============================================================================

async function loadResults() {
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/parse/results/${currentJobId}`);

        if (response.status === 404) {
            showError('Results not found. The job may not exist or results may have expired.');
            return;
        }

        if (response.status === 202) {
            const data = await response.json();
            showError(`Job is still processing. Please wait and refresh the page. Status: ${data.error}`);
            return;
        }

        if (response.status === 500) {
            const data = await response.json();
            showError(`Parsing failed: ${data.detail.message}`);
            return;
        }

        if (!response.ok) {
            throw new Error(`Failed to load results: ${response.statusText}`);
        }

        currentResults = await response.json();
        displayResults(currentResults);
        hideLoading();

    } catch (error) {
        showError(`Error loading results: ${error.message}`);
    }
}

// ============================================================================
// Display Results
// ============================================================================

function displayResults(results) {
    // Display metadata
    displayMetadata(results.metadata);

    // Display statistics
    displayStatistics(results.statistics);

    // Display markdown
    document.getElementById('markdownContent').value = results.content.markdown;

    // Store data for later use
    currentTexts = results.content.texts || [];
    currentTables = results.content.tables || [];

    // Display text items
    displayTexts(currentTexts);

    // Display tables
    displayTables(currentTables, 'dict');

    // Display images
    displayImages(results.content.pictures || []);

    // Setup filters
    setupFilters(results);
}

// ============================================================================
// Metadata Display
// ============================================================================

function displayMetadata(metadata) {
    const table = document.getElementById('metadataTable');

    const processingTime = metadata.processing_time_ms
        ? `${(metadata.processing_time_ms / 1000).toFixed(2)}s`
        : 'N/A';

    const fileSize = metadata.file_size_bytes
        ? formatBytes(metadata.file_size_bytes)
        : 'N/A';

    table.innerHTML = `
        <tr>
            <td><strong>Filename</strong></td>
            <td>${metadata.filename}</td>
        </tr>
        <tr>
            <td><strong>File Size</strong></td>
            <td>${fileSize}</td>
        </tr>
        <tr>
            <td><strong>MIME Type</strong></td>
            <td>${metadata.mimetype || 'N/A'}</td>
        </tr>
        <tr>
            <td><strong>Page Count</strong></td>
            <td>${metadata.page_count}</td>
        </tr>
        <tr>
            <td><strong>Processing Time</strong></td>
            <td>${processingTime}</td>
        </tr>
        <tr>
            <td><strong>Parsed At</strong></td>
            <td>${new Date(metadata.parsed_at).toLocaleString()}</td>
        </tr>
        ${metadata.binary_hash ? `
        <tr>
            <td><strong>Binary Hash</strong></td>
            <td style="font-family: monospace; font-size: 0.85rem;">${metadata.binary_hash}</td>
        </tr>
        ` : ''}
    `;
}

// ============================================================================
// Statistics Display
// ============================================================================

function displayStatistics(stats) {
    document.getElementById('textCount').textContent = stats.total_text_items;
    document.getElementById('tableCount').textContent = stats.total_tables;
    document.getElementById('imageCount').textContent = stats.total_pictures;
}

// ============================================================================
// Text Items Display
// ============================================================================

function displayTexts(texts) {
    const container = document.getElementById('textItemsList');

    if (texts.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No text items found.</p>';
        return;
    }

    container.innerHTML = texts.map(text => `
        <div class="text-item">
            <div class="text-label">${text.label || 'unknown'}</div>
            <div class="text-content">${escapeHtml(text.text)}</div>
            ${text.page !== null || text.bbox ? `
                <div class="text-meta">
                    ${text.page !== null ? `Page ${text.page}` : ''}
                    ${text.bbox ? ` | Position: (${text.bbox.left.toFixed(0)}, ${text.bbox.top.toFixed(0)})` : ''}
                </div>
            ` : ''}
        </div>
    `).join('');
}

// ============================================================================
// Tables Display
// ============================================================================

function displayTables(tables, format = 'dict') {
    const container = document.getElementById('tablesContainer');

    if (tables.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No tables found.</p>';
        return;
    }

    container.innerHTML = tables.map((table, index) => {
        let tableHtml = `
            <div class="card mt-2">
                <h3 class="card-subtitle">Table ${index + 1}</h3>
                ${table.page !== null ? `<p class="text-muted">Page ${table.page}</p>` : ''}
                ${table.rows && table.columns ? `<p class="text-muted">${table.rows} rows × ${table.columns} columns</p>` : ''}
        `;

        if (format === 'csv' && table.dataframe_csv) {
            tableHtml += `
                <div class="form-group mt-2">
                    <textarea rows="10" readonly style="font-family: monospace; font-size: 0.85rem;">${escapeHtml(table.dataframe_csv)}</textarea>
                </div>
            `;
        } else if (table.data) {
            tableHtml += `
                <div class="table-container mt-2">
                    ${renderTableData(table.data)}
                </div>
            `;
        }

        tableHtml += '</div>';
        return tableHtml;
    }).join('');
}

function renderTableData(data) {
    // Convert data object to HTML table
    if (!data || typeof data !== 'object') {
        return '<p class="text-muted">No table data available</p>';
    }

    // Get column names
    const columns = Object.keys(data);
    if (columns.length === 0) {
        return '<p class="text-muted">Empty table</p>';
    }

    // Get number of rows
    const firstColumn = data[columns[0]];
    const rowCount = Object.keys(firstColumn).length;

    let tableHtml = '<table><thead><tr>';

    // Headers
    columns.forEach(col => {
        tableHtml += `<th>${escapeHtml(col)}</th>`;
    });
    tableHtml += '</tr></thead><tbody>';

    // Rows
    for (let i = 0; i < rowCount; i++) {
        tableHtml += '<tr>';
        columns.forEach(col => {
            const value = data[col][i] !== null && data[col][i] !== undefined
                ? data[col][i]
                : '';
            tableHtml += `<td>${escapeHtml(String(value))}</td>`;
        });
        tableHtml += '</tr>';
    }

    tableHtml += '</tbody></table>';
    return tableHtml;
}

// ============================================================================
// Images Display
// ============================================================================

function displayImages(images) {
    const container = document.getElementById('imagesContainer');

    if (images.length === 0) {
        container.innerHTML = '<p class="text-muted text-center">No images found.</p>';
        return;
    }

    container.innerHTML = images.map(image => `
        <div class="image-item">
            ${image.image_uri ? `
                <img src="${image.image_uri}" alt="${image.caption || 'Image'}" />
            ` : `
                <div style="height: 200px; display: flex; align-items: center; justify-content: center; background: var(--bg-tertiary);">
                    <span class="text-muted">No image data</span>
                </div>
            `}
            <div class="image-caption">
                ${image.caption ? `
                    <div class="image-description"><strong>Caption:</strong> ${escapeHtml(image.caption)}</div>
                ` : ''}
                ${image.description ? `
                    <div class="image-description">
                        <strong>AI Description:</strong> ${escapeHtml(image.description)}
                        ${image.description_provider ? `
                            <span class="status-badge status-processing" style="margin-left: 0.5rem; font-size: 0.75rem;">
                                ${image.description_provider}
                            </span>
                        ` : ''}
                    </div>
                ` : ''}
                <div class="image-meta">
                    ID: ${image.id}
                    ${image.page !== null ? ` | Page ${image.page}` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

// ============================================================================
// Filters
// ============================================================================

function setupFilters(results) {
    // Page filter
    const pageFilter = document.getElementById('pageFilter');
    const pages = new Set();

    currentTexts.forEach(text => {
        if (text.page !== null) {
            pages.add(text.page);
        }
    });

    const sortedPages = Array.from(pages).sort((a, b) => a - b);
    pageFilter.innerHTML = '<option value="">All Pages</option>' +
        sortedPages.map(page => `<option value="${page}">Page ${page}</option>`).join('');

    // Label filter
    const labelFilter = document.getElementById('labelFilter');
    const labels = new Set();

    currentTexts.forEach(text => {
        if (text.label) {
            labels.add(text.label);
        }
    });

    const sortedLabels = Array.from(labels).sort();
    labelFilter.innerHTML = '<option value="">All Labels</option>' +
        sortedLabels.map(label => `<option value="${label}">${label}</option>`).join('');
}

async function applyTextFilters() {
    const page = document.getElementById('pageFilter').value;
    const label = document.getElementById('labelFilter').value;

    if (!page && !label) {
        // No filters, show all
        displayTexts(currentTexts);
        return;
    }

    // Build query params
    const params = new URLSearchParams();
    if (page) params.append('page', page);
    if (label) params.append('label', label);

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/parse/results/${currentJobId}/texts?${params}`);
        const data = await response.json();

        displayTexts(data.texts);

    } catch (error) {
        console.error('Filter error:', error);
        displayTexts(currentTexts); // Fallback to client-side filtering
    }
}

async function loadTables(format) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/parse/results/${currentJobId}/tables?format=${format}`);
        const data = await response.json();

        displayTables(data.tables, format);

    } catch (error) {
        console.error('Load tables error:', error);
    }
}

// ============================================================================
// Export Functions
// ============================================================================

async function exportMarkdown() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/parse/results/${currentJobId}/export/markdown`);
        const markdown = await response.text();

        // Download as file
        downloadFile(markdown, `${currentJobId}_export.md`, 'text/markdown');

    } catch (error) {
        alert(`Export failed: ${error.message}`);
    }
}

async function exportJSON() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/parse/results/${currentJobId}/export/json`);
        const json = await response.json();

        // Download as file
        const jsonString = JSON.stringify(json, null, 2);
        downloadFile(jsonString, `${currentJobId}_export.json`, 'application/json');

    } catch (error) {
        alert(`Export failed: ${error.message}`);
    }
}

// ============================================================================
// Utility Functions
// ============================================================================

function showLoading() {
    document.getElementById('loadingIndicator').classList.remove('hidden');
    document.querySelectorAll('.card:not(#loadingIndicator)').forEach(card => {
        card.style.display = 'none';
    });
}

function hideLoading() {
    document.getElementById('loadingIndicator').classList.add('hidden');
    document.querySelectorAll('.card').forEach(card => {
        card.style.display = 'block';
    });
}

function showError(message) {
    hideLoading();
    document.getElementById('errorMessage').classList.remove('hidden');
    document.getElementById('errorText').textContent = message;
    document.querySelectorAll('.card:not(#errorMessage):not(#loadingIndicator)').forEach(card => {
        card.style.display = 'none';
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
