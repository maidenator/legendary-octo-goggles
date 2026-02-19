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

// Listen for camera input
cameraInput.addEventListener('change', handleImageCapture);

function handleImageCapture(event) {
    const file = event.target.files[0];
    
    if (!file) {
        return;
    }

    // Show loading status
    showStatus('Processing image...', 'text-blue-600');

    // Create FileReader to load image
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const img = new Image();
        
        img.onload = function() {
            // Compress the image
            compressImage(img, file.name);
        };
        
        img.onerror = function() {
            showStatus('Error loading image. Please try again.', 'text-red-600');
        };
        
        img.src = e.target.result;
    };
    
    reader.onerror = function() {
        showStatus('Error reading file. Please try again.', 'text-red-600');
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
        function(blob) {
            if (!blob) {
                showStatus('Compression failed. Please try again.', 'text-red-600');
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
            
            showStatus('Image ready to send!', 'text-green-600');
        },
        'image/jpeg',
        JPEG_QUALITY
    );
}

function displayPreview(blob) {
    // Create object URL for preview
    const objectUrl = URL.createObjectURL(blob);
    previewImage.src = objectUrl;
    previewSection.classList.remove('hidden');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function showStatus(message, colorClass) {
    statusMessage.textContent = message;
    statusMessage.className = `mt-4 text-center text-sm ${colorClass}`;
}

// Mock submit handler
sendButton.addEventListener('click', function() {
    if (!compressedFile) {
        showStatus('No image to send. Please scan first.', 'text-red-600');
        return;
    }
    
    // Log file size for verification
    console.log('=== Image Compression Results ===');
    console.log('Compressed file size:', formatFileSize(compressedFile.size));
    console.log('File name:', compressedFile.name);
    console.log('File type:', compressedFile.type);
    console.log('Dimensions:', `${previewImage.naturalWidth} x ${previewImage.naturalHeight}`);
    console.log('================================');
    
    showStatus(`File ready! Size: ${formatFileSize(compressedFile.size)} (check console for details)`, 'text-green-600');
    
    // TODO: In Module 2, replace this with actual Fetch API call to FastAPI server
});
