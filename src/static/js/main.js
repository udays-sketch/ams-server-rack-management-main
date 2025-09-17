// Main JavaScript for Server Rack Change Detection Web App

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // File upload functionality
    const fileUploads = document.querySelectorAll('.file-upload');
    
    fileUploads.forEach(upload => {
        const input = upload.querySelector('input[type="file"]');
        const preview = upload.querySelector('.file-preview');
        
        upload.addEventListener('click', () => {
            input.click();
        });
        
        if (input) {
            input.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        if (preview) {
                            preview.innerHTML = `<img src="${e.target.result}" alt="Preview" class="img-fluid">`;
                            preview.style.display = 'block';
                            
                            // Hide the upload icon and text when preview is shown
                            const uploadIcon = upload.querySelector('.file-upload-icon');
                            const uploadText = upload.querySelector('.file-upload-text');
                            
                            if (uploadIcon) uploadIcon.style.display = 'none';
                            if (uploadText) uploadText.style.display = 'none';
                        }
                    };
                    
                    reader.readAsDataURL(this.files[0]);
                    
                    // Update file name display if it exists
                    const fileNameDisplay = upload.querySelector('.file-name');
                    if (fileNameDisplay) {
                        fileNameDisplay.textContent = this.files[0].name;
                    }
                }
            });
        }
    });
    
    // Image comparison slider if present
    const sliders = document.querySelectorAll('.comparison-slider');
    
    sliders.forEach(slider => {
        const sliderHandle = slider.querySelector('.slider-handle');
        const beforeImage = slider.querySelector('.before-image');
        
        if (sliderHandle && beforeImage) {
            let isDragging = false;
            
            const moveSlider = (e) => {
                if (!isDragging) return;
                
                const sliderRect = slider.getBoundingClientRect();
                const x = e.clientX - sliderRect.left;
                const percent = (x / sliderRect.width) * 100;
                
                // Constrain to slider bounds
                const boundedPercent = Math.max(0, Math.min(100, percent));
                
                sliderHandle.style.left = `${boundedPercent}%`;
                beforeImage.style.width = `${boundedPercent}%`;
            };
            
            sliderHandle.addEventListener('mousedown', () => {
                isDragging = true;
            });
            
            window.addEventListener('mouseup', () => {
                isDragging = false;
            });
            
            slider.addEventListener('mousemove', moveSlider);
            
            // Touch support
            sliderHandle.addEventListener('touchstart', (e) => {
                isDragging = true;
                e.preventDefault();
            });
            
            window.addEventListener('touchend', () => {
                isDragging = false;
            });
            
            slider.addEventListener('touchmove', (e) => {
                if (!isDragging) return;
                
                const touch = e.touches[0];
                const sliderRect = slider.getBoundingClientRect();
                const x = touch.clientX - sliderRect.left;
                const percent = (x / sliderRect.width) * 100;
                
                // Constrain to slider bounds
                const boundedPercent = Math.max(0, Math.min(100, percent));
                
                sliderHandle.style.left = `${boundedPercent}%`;
                beforeImage.style.width = `${boundedPercent}%`;
                
                e.preventDefault();
            });
        }
    });
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
    
    // Tabs functionality
    const tabLinks = document.querySelectorAll('.tab-link');
    
    tabLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetTab = document.querySelector(targetId);
            
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Deactivate all tab links
            tabLinks.forEach(link => {
                link.classList.remove('active');
            });
            
            // Activate clicked tab and link
            targetTab.classList.add('active');
            this.classList.add('active');
        });
    });
    
    // Initialize tooltips if Bootstrap is used
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltips.forEach(tooltip => {
            new bootstrap.Tooltip(tooltip);
        });
    }
    
    // AJAX form submission for image comparison
    const compareForm = document.getElementById('compare-form');
    
    if (compareForm) {
        compareForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const resultsContainer = document.getElementById('comparison-results');
            const loadingIndicator = document.getElementById('loading-indicator');
            
            if (loadingIndicator) loadingIndicator.style.display = 'block';
            if (resultsContainer) resultsContainer.innerHTML = '';
            
            fetch('/api/compare', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (loadingIndicator) loadingIndicator.style.display = 'none';
                
                if (data.success) {
                    // if (resultsContainer) {
                    //     resultsContainer.innerHTML = `
                    //         <div class="alert alert-success">
                    //             <strong>Success!</strong> Images compared successfully.
                    //         </div>
                    //         <div class="image-comparison-result">
                    //             <img src="${data.comparison_image}" alt="Comparison Result" class="img-fluid">
                    //         </div>
                    //         <div class="changes-detected mt-4">
                    //             <h4>Changes Detected: ${data.changes.length}</h4>
                    //             <ul class="change-list">
                    //                 ${data.changes.map(change => `
                    //                     <li class="change-item">
                    //                         <span class="change-type ${change.type.toLowerCase()}">${change.type}</span>
                    //                         <div class="change-details">
                    //                             <div>Location: RU ${change.location.estimated_ru}</div>
                    //                             <div class="change-confidence">Confidence: ${(change.confidence * 100).toFixed(2)}%</div>
                    //                         </div>
                    //                     </li>
                    //                 `).join('')}
                    //             </ul>
                    //         </div>
                    //         <div class="mt-4">
                    //             <button class="btn btn-primary" id="reconcile-btn">Reconcile with AMS</button>
                    //         </div>
                    //     `;
                        
                    //     // Add event listener to reconcile button
                    //     const reconcileBtn = document.getElementById('reconcile-btn');
                    //     if (reconcileBtn) {
                    //         reconcileBtn.addEventListener('click', function() {
                    //             reconcileChanges(data.changes_id);
                    //         });
                    //     }
                    // }
                } else {
                    // if (resultsContainer) {
                    //     resultsContainer.innerHTML = `
                    //         <div class="alert alert-danger">
                    //             <strong>Error!</strong> ${data.message || 'Failed to compare images.'}
                    //         </div>
                    //     `;
                    // }
                }
            })
            .catch(error => {
                if (loadingIndicator) loadingIndicator.style.display = 'none';
                
                // if (resultsContainer) {
                //     resultsContainer.innerHTML = `
                //         <div class="alert alert-danger">
                //             <strong>Error!</strong> An unexpected error occurred.
                //         </div>
                //     `;
                // }
                console.error('Error:', error);
            });
        });
    }
    
    // Function to reconcile changes with AMS
    function reconcileChanges(changesId) {
        const resultsContainer = document.getElementById('reconciliation-results');
        const loadingIndicator = document.getElementById('reconciliation-loading');
        
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        if (resultsContainer) resultsContainer.innerHTML = '';
        
        fetch(`/reconcile/${changesId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            
            if (data.success) {
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="alert alert-success">
                            <strong>Success!</strong> Reconciliation completed.
                        </div>
                        <div class="card">
                            <div class="card-header">
                                <h4>Discrepancies Found: ${data.discrepancies.length}</h4>
                            </div>
                            <div class="card-body">
                                <div class="table-container">
                                    <table class="table">
                                        <thead>
                                            <tr>
                                                <th>ID</th>
                                                <th>Type</th>
                                                <th>Location</th>
                                                <th>Severity</th>
                                                <th>Action</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${data.discrepancies.map(d => `
                                                <tr>
                                                    <td>${d.discrepancy_id}</td>
                                                    <td>${d.type}</td>
                                                    <td>RU ${d.location.ru_position}</td>
                                                    <td><span class="badge bg-${getSeverityClass(d.severity)}">${d.severity}</span></td>
                                                    <td>
                                                        <button class="btn btn-sm btn-primary view-discrepancy" data-id="${d.discrepancy_id}">View</button>
                                                    </td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div class="card-footer">
                                <a href="/report/${data.report_id}" class="btn btn-success" target="_blank">View Full Report</a>
                            </div>
                        </div>
                    `;
                    
                    // Add event listeners to view buttons
                    document.querySelectorAll('.view-discrepancy').forEach(btn => {
                        btn.addEventListener('click', function() {
                            const discrepancyId = this.getAttribute('data-id');
                            viewDiscrepancyDetails(discrepancyId);
                        });
                    });
                }
            } else {
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="alert alert-danger">
                            <strong>Error!</strong> ${data.message || 'Failed to reconcile changes.'}
                        </div>
                    `;
                }
            }
        })
        .catch(error => {
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            
            if (resultsContainer) {
                resultsContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error!</strong> An unexpected error occurred.
                    </div>
                `;
            }
            console.error('Error:', error);
        });
    }
    
    // Function to view discrepancy details
    function viewDiscrepancyDetails(discrepancyId) {
        const modal = document.getElementById('discrepancy-modal');
        const modalContent = document.getElementById('discrepancy-modal-content');
        
        if (!modal || !modalContent) return;
        
        fetch(`/discrepancy/${discrepancyId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                modalContent.innerHTML = `
                    <div class="discrepancy-details">
                        <h3>${data.discrepancy.type}</h3>
                        <p><strong>Description:</strong> ${data.discrepancy.description}</p>
                        <p><strong>Location:</strong> Rack ${data.discrepancy.location.rack_id}, RU ${data.discrepancy.location.ru_position}</p>
                        <p><strong>Severity:</strong> <span class="badge bg-${getSeverityClass(data.discrepancy.severity)}">${data.discrepancy.severity}</span></p>
                        <p><strong>Confidence:</strong> ${(data.discrepancy.confidence * 100).toFixed(2)}%</p>
                        
                        <div class="row mt-4">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header">
                                        <h5>AMS Data</h5>
                                    </div>
                                    <div class="card-body">
                                        <pre>${data.discrepancy.ams_data ? JSON.stringify(data.discrepancy.ams_data, null, 2) : 'No AMS data available'}</pre>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header">
                                        <h5>Detected Change</h5>
                                    </div>
                                    <div class="card-body">
                                        <pre>${JSON.stringify(data.discrepancy.detected_data, null, 2)}</pre>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mt-4">
                            <h4>Recommended Action</h4>
                            <p>${data.discrepancy.recommended_action}</p>
                            <button class="btn btn-primary resolve-btn" data-id="${data.discrepancy.discrepancy_id}">Resolve Discrepancy</button>
                        </div>
                    </div>
                `;
                
                // Show modal
                modal.style.display = 'block';
                
                // Add event listener to resolve button
                const resolveBtn = modal.querySelector('.resolve-btn');
                if (resolveBtn) {
                    resolveBtn.addEventListener('click', function() {
                        resolveDiscrepancy(this.getAttribute('data-id'));
                        modal.style.display = 'none';
                    });
                }
                
                // Add close functionality
                const closeBtn = modal.querySelector('.close');
                if (closeBtn) {
                    closeBtn.addEventListener('click', function() {
                        modal.style.display = 'none';
                    });
                }
                
                // Close when clicking outside
                window.addEventListener('click', function(event) {
                    if (event.target === modal) {
                        modal.style.display = 'none';
                    }
                });
            } else {
                alert('Failed to load discrepancy details.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred.');
        });
    }
    
    // Function to resolve discrepancy
    function resolveDiscrepancy(discrepancyId) {
        fetch(`/resolve-discrepancy/${discrepancyId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Discrepancy resolved successfully!');
                // Refresh the discrepancies list if needed
                // This could trigger a re-fetch of the reconciliation data
            } else {
                alert(`Failed to resolve discrepancy: ${data.message || 'Unknown error'}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An unexpected error occurred.');
        });
    }
    
    // Helper function to get severity class
    function getSeverityClass(severity) {
        switch (severity.toLowerCase()) {
            case 'high':
                return 'danger';
            case 'medium':
                return 'warning';
            case 'low':
                return 'success';
            default:
                return 'secondary';
        }
    }
});
