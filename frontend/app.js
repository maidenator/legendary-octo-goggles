// Ayahay SmartScan - Frontend Image Compression & Upload Handler

const cameraInput = document.getElementById('camera-input');
const previewSection = document.getElementById('preview-section');
const previewImage = document.getElementById('preview-image');
const fileSizeInfo = document.getElementById('file-size-info');
const sendButton = document.getElementById('send-button');
const statusMessage = document.getElementById('status-message');

// Configuration
const MAX_WIDTH = 1500;
const JPEG_QUALITY = 0.8;

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

        // Show success
        showStatus(`Success! Image received by server. Size: ${formatFileSize(result.size_bytes)}`, 'success');
        console.log('Server response:', result);

        // Reset button
        sendButton.textContent = 'Send to Server';
        sendButton.disabled = false;

    } catch (error) {
        console.error('Upload error:', error);
        showStatus(`Error: ${error.message}. Make sure the server is running.`, 'error');

        // Reset button
        sendButton.textContent = 'Send to Server';
        sendButton.disabled = false;
    }
});
