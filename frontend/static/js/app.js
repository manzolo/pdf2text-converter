// API Configuration
const API_BASE = '/api';

// State
let selectedFile = null;
let currentResult = null;

// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const optionsSection = document.getElementById('optionsSection');
const processBtn = document.getElementById('processBtn');
const cancelBtn = document.getElementById('cancelBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const extractedText = document.getElementById('extractedText');
const metadata = document.getElementById('metadata');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAPIStatus();
    setupEventListeners();
});

// Check API Status
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();

        document.getElementById('apiStatus').textContent = 'Online';
        document.getElementById('apiStatus').classList.add('online');
        document.getElementById('gpuStatus').textContent = data.processor.gpu_enabled ? 'Enabled' : 'Disabled';
        document.getElementById('extractionMethod').textContent = data.processor.extraction_method;
        document.getElementById('maxFileSize').textContent = data.max_file_size_mb;
    } catch (error) {
        document.getElementById('apiStatus').textContent = 'Offline';
        document.getElementById('apiStatus').classList.add('offline');
        console.error('API Status check failed:', error);
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // File upload
    browseBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('click', (e) => {
        if (e.target === uploadArea || e.target.closest('.upload-area')) {
            fileInput.click();
        }
    });

    // Processing
    processBtn.addEventListener('click', processFile);
    cancelBtn.addEventListener('click', resetUpload);

    // Results actions
    document.getElementById('copyBtn').addEventListener('click', copyToClipboard);
    document.getElementById('downloadBtn').addEventListener('click', downloadText);
    document.getElementById('newFileBtn').addEventListener('click', resetAll);
    document.getElementById('retryBtn').addEventListener('click', resetAll);
}

// File Selection Handlers
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        validateAndSetFile(file);
    }
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');

    const file = e.dataTransfer.files[0];
    if (file) {
        validateAndSetFile(file);
    }
}

function validateAndSetFile(file) {
    // Check if it's a PDF
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showError('Please select a PDF file.');
        return;
    }

    // Check file size
    const maxSize = parseInt(document.getElementById('maxFileSize').textContent) * 1024 * 1024;
    if (file.size > maxSize) {
        showError(`File is too large. Maximum size is ${maxSize / (1024 * 1024)}MB.`);
        return;
    }

    selectedFile = file;
    showOptions();
}

function showOptions() {
    uploadArea.style.display = 'none';
    optionsSection.style.display = 'block';
}

function resetUpload() {
    selectedFile = null;
    fileInput.value = '';
    uploadArea.style.display = 'block';
    optionsSection.style.display = 'none';
}

// Process File
async function processFile() {
    if (!selectedFile) return;

    const useOcr = document.getElementById('useOcrCheckbox').checked;
    const chunkProcessing = document.getElementById('chunkProcessingCheckbox').checked;
    const removeRepetitive = document.getElementById('removeRepetitiveCheckbox').checked;
    const removeCopyright = document.getElementById('removeCopyrightCheckbox').checked;
    const language = document.getElementById('languageSelect').value;
    const processingMode = document.querySelector('input[name="processingMode"]:checked').value;

    // Hide options, show progress
    optionsSection.style.display = 'none';
    progressSection.style.display = 'block';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';

    try {
        if (processingMode === 'streaming') {
            await processFileStreaming(useOcr, language, removeRepetitive, removeCopyright);
        } else {
            await processFileStandard(useOcr, chunkProcessing, language, removeRepetitive, removeCopyright);
        }
    } catch (error) {
        showError(`Processing failed: ${error.message}`);
    }
}

// Standard Processing
async function processFileStandard(useOcr, chunkProcessing, language, removeRepetitive, removeCopyright) {
    updateProgress(0, 'Uploading file...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    const url = `${API_BASE}/extract?use_ocr=${useOcr}&chunk_processing=${chunkProcessing}&language=${language}&remove_repetitive=${removeRepetitive}&remove_copyright=${removeCopyright}`;

    const response = await fetch(url, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Processing failed');
    }

    updateProgress(50, 'Processing PDF...');

    const result = await response.json();

    updateProgress(100, 'Complete!');

    setTimeout(() => {
        showResults(result);
    }, 500);
}

// Streaming Processing
async function processFileStreaming(useOcr, language, removeRepetitive, removeCopyright) {
    updateProgress(0, 'Starting streaming process...');

    const formData = new FormData();
    formData.append('file', selectedFile);

    const url = `${API_BASE}/extract-stream?use_ocr=${useOcr}&language=${language}`;

    const response = await fetch(url, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Processing failed');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let allText = [];
    let totalPages = 0;

    while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
            if (line.trim()) {
                const chunk = JSON.parse(line);
                totalPages = chunk.total_pages;
                allText.push(chunk.text);

                updateProgress(chunk.progress, `Processing page ${chunk.page} of ${chunk.total_pages}...`);
            }
        }
    }

    // Show results
    showResults({
        success: true,
        filename: selectedFile.name,
        pages: totalPages,
        text: allText.join('\n\n'),
        total_chars: allText.join('').length,
        chunks_processed: totalPages
    });
}

// Update Progress
function updateProgress(percent, message) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = message;
}

// Show Results
function showResults(result) {
    currentResult = result;

    progressSection.style.display = 'none';
    resultsSection.style.display = 'block';

    // Update metadata
    metadata.innerHTML = `
        <div class="metadata-item">
            <span class="metadata-label">Filename</span>
            <span class="metadata-value">${result.filename}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Pages</span>
            <span class="metadata-value">${result.pages}</span>
        </div>
        <div class="metadata-item">
            <span class="metadata-label">Total Characters</span>
            <span class="metadata-value">${result.total_chars.toLocaleString()}</span>
        </div>
        ${result.chunks_processed ? `
        <div class="metadata-item">
            <span class="metadata-label">Chunks Processed</span>
            <span class="metadata-value">${result.chunks_processed}</span>
        </div>
        ` : ''}
    `;

    // Show extracted text
    extractedText.textContent = result.text;
}

// Show Error
function showError(message) {
    optionsSection.style.display = 'none';
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'block';
    errorMessage.textContent = message;
}

// Copy to Clipboard
async function copyToClipboard() {
    if (!currentResult) return;

    try {
        await navigator.clipboard.writeText(currentResult.text);
        alert('Text copied to clipboard!');
    } catch (error) {
        console.error('Copy failed:', error);
        alert('Failed to copy text.');
    }
}

// Download as TXT
function downloadText() {
    if (!currentResult) return;

    const blob = new Blob([currentResult.text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentResult.filename.replace('.pdf', '')}_extracted.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Reset All
function resetAll() {
    selectedFile = null;
    currentResult = null;
    fileInput.value = '';

    uploadArea.style.display = 'block';
    optionsSection.style.display = 'none';
    progressSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';

    progressFill.style.width = '0%';
}
