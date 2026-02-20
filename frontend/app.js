// Ayahay SmartScan - Frontend Image Compression & Upload Handler

const cameraInput = document.getElementById('camera-input');
const previewSection = document.getElementById('preview-section');
const previewImage = document.getElementById('preview-image');
const fileSizeInfo = document.getElementById('file-size-info');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');

// History Table Elements
const historySection = document.getElementById('history-section');
const historyTableBody = document.getElementById('history-table-body');
const historyLoading = document.getElementById('history-loading');

// Configuration
const MAX_WIDTH = 2500;
const JPEG_QUALITY = 0.95;
const SERVER_URL = window.SERVER_URL || 'http://localhost:8000';

let compressedFile = null;
let currentObjectUrl = null;  // Track object URL for cleanup

// Listen for camera input
cameraInput.addEventListener('change', handleImageCapture);

function handleImageCapture(event) {
    const file = event.target.files[0];

    if (!file) {
        return;
    }

    // Show loading status
    showStatus('Processing image...', 'info');

    // Create FileReader to load image
    const reader = new FileReader();

    reader.onload = function (e) {
        const img = new Image();

        img.onload = function () {
            // Compress the image
            compressImage(img, file.name);
        };

        img.onerror = function () {
            showStatus('Error loading image. Please try again.', 'error');
        };

        img.src = e.target.result;
    };

    reader.onerror = function () {
        showStatus('Error reading file. Please try again.', 'error');
    };

    reader.readAsDataURL(file);
}

function compressImage(img, originalFileName) {
    // Create canvas element (invisible)
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    // Calculate new dimensions
    let width = img.width;
    let height = img.height;

    if (width > MAX_WIDTH) {
        height = (height * MAX_WIDTH) / width;
        width = MAX_WIDTH;
    }

    // Set canvas dimensions
    canvas.width = width;
    canvas.height = height;

    // Fill with white background (crucial for transparent PNGs converted to JPEG!)
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, width, height);

    // Draw image to canvas
    ctx.drawImage(img, 0, 0, width, height);

    // Convert to blob with JPEG compression
    canvas.toBlob(
        function (blob) {
            if (!blob) {
                showStatus('Compression failed. Please try again.', 'error');
                return;
            }

            // Create File object from blob
            compressedFile = new File([blob], originalFileName, {
                type: 'image/jpeg',
                lastModified: Date.now()
            });

            // Display preview
            displayPreview(blob);

            // Show file size info
            const originalSize = cameraInput.files[0].size;
            const compressedSize = blob.size;
            const compressionRatio = ((1 - compressedSize / originalSize) * 100).toFixed(1);

            fileSizeInfo.textContent =
                `Original: ${formatFileSize(originalSize)} → Compressed: ${formatFileSize(compressedSize)} (${compressionRatio}% reduction)`;

            // Enable send button
            sendButton.disabled = false;
            sendButton.classList.remove('hidden');

            showStatus('Image ready to send!', 'success');
        },
        'image/jpeg',
        JPEG_QUALITY
    );
}

function displayPreview(blob) {
    // Revoke the previous object URL to prevent memory leak
    if (currentObjectUrl) {
        URL.revokeObjectURL(currentObjectUrl);
    }
    currentObjectUrl = URL.createObjectURL(blob);
    previewImage.src = currentObjectUrl;
    previewSection.classList.remove('hidden');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showStatus(message, type) {
    statusMessage.textContent = message;
    // Use inline style for color to avoid Tailwind purge issues with dynamic classes
    const colors = { success: '#16a34a', error: '#dc2626', info: '#2563eb' };
    statusMessage.style.color = colors[type] || '#374151';
}

// Send to server handler
sendButton.addEventListener('click', async function () {
    if (!compressedFile) {
        showStatus('No image to send. Please scan first.', 'error');
        return;
    }

    // Disable button during upload
    sendButton.disabled = true;
    sendButton.textContent = 'Sending...';
    showStatus('Sending image to server...', 'info');

    try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('file', compressedFile);

        // Get server URL (default to localhost, but can be configured)
        const serverUrl = window.SERVER_URL || 'http://localhost:8000';

        // Send to FastAPI server
        const response = await fetch(`${serverUrl}/scan`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Server error');
        }

        const result = await response.json();

        // Parse detailed OCR response for status messages
        const ocr = result.ocr_result;
        if (ocr && ocr.container_id) {
            if (ocr.validation_status === 'valid') {
                showStatus(`Success! Found VALID Container ID: ${ocr.container_id}`, 'success');
            } else {
                showStatus(`Warning: Found INVALID check-digit for ID: ${ocr.container_id}`, 'error');
            }
        } else {
            showStatus(`No Container ID could be found in the image.`, 'info');
        }

        console.log('Server response:', result);

        // Reset button
        sendButton.textContent = 'Send to Server';
        sendButton.disabled = false;

        // Auto-refresh the scan history table!
        fetchScanHistory();

    } catch (error) {
        console.error('Upload error:', error);
        showStatus(`Error: ${error.message}. Make sure the server is running.`, 'error');

        // Reset button
        sendButton.textContent = 'Send to Server';
        sendButton.disabled = false;
    }
});

// ---------------------------------------------------------------------------
// Scan History Dashboard Logic
// ---------------------------------------------------------------------------

function formatTimestamp(isoString) {
    if (!isoString) return 'Unknown';
    // The backend saves timestamps like "20260220_074401"
    // We will parse it simply or fall back to the raw string if parsing fails
    if (isoString.length === 15 && isoString.includes('_')) {
        const year = isoString.substring(0, 4);
        const month = isoString.substring(4, 6);
        const day = isoString.substring(6, 8);
        const hour = isoString.substring(9, 11);
        const min = isoString.substring(11, 13);
        const sec = isoString.substring(13, 15);
        return `${year}-${month}-${day} ${hour}:${min}:${sec}`;
    }
    return isoString;
}

function getBadgeHtml(status) {
    if (status === 'valid') {
        return '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Valid</span>';
    } else if (status === 'invalid') {
        return '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Invalid</span>';
    } else {
        return '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">Not Found</span>';
    }
}

async function fetchScanHistory() {
    try {
        historySection.classList.remove('hidden');
        historyLoading.classList.remove('hidden');
        historyTableBody.innerHTML = ''; // Clear existing text

        const response = await fetch(`${SERVER_URL}/scans?limit=50`);
        if (!response.ok) throw new Error('Failed to fetch history');

        const data = await response.json();

        historyLoading.classList.add('hidden');

        if (data.scans.length === 0) {
            historyTableBody.innerHTML = `<tr><td colspan="4" class="px-6 py-4 text-center text-sm text-gray-500">No scans found in database.</td></tr>`;
            return;
        }

        // Generate rows
        data.scans.forEach(scan => {
            const tr = document.createElement('tr');
            tr.className = "hover:bg-gray-50";

            const dateStr = formatTimestamp(scan.timestamp);
            const sizeStr = formatFileSize(scan.size_bytes);
            const badge = getBadgeHtml(scan.validation_status);
            const containerDisplay = scan.container_id ? `<span class="font-mono font-medium">${scan.container_id}</span>` : '<span class="text-gray-400 italic">None</span>';

            tr.innerHTML = `
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">${dateStr}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-l border-gray-100">${scan.filename}<br><span class="text-xs text-gray-500">${sizeStr}</span></td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-l border-gray-100">${containerDisplay}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm border-l border-gray-100">${badge}</td>
            `;

            historyTableBody.appendChild(tr);
        });

    } catch (error) {
        console.error("Error fetching history:", error);
        historyLoading.classList.add('hidden');
        historyTableBody.innerHTML = `<tr><td colspan="4" class="px-6 py-4 text-center text-sm text-red-500">Failed to load database history.</td></tr>`;
    }
}

// Load history immediately on page load
fetchScanHistory();
