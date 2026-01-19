/**
 * UI Gateway - Enhanced JavaScript with Animations
 * Uses Fetch API for async operations
 */

// Initialize animations on page load
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(flash => {
        flash.classList.add('animate-slideDown');
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-20px)';
            setTimeout(() => flash.remove(), 300);
        }, 5000);
    });

    // Add staggered animations to cards
    const cards = document.querySelectorAll('.card, .feature-card, .stat-card');
    cards.forEach((card, index) => {
        card.classList.add('animate-fadeIn');
        if (index < 8) {
            card.classList.add(`stagger-${index + 1}`);
        }
    });

    // Add animations to stat values on load
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(stat => {
        animateValue(stat, 0, parseInt(stat.textContent) || 0, 1500);
    });

    // Setup intersection observer for scroll animations
    setupScrollAnimations();

    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.02)';
        });
        btn.addEventListener('mouseleave', function() {
            this.style.transform = '';
        });
    });

    // Add animations to table rows
    const tableRows = document.querySelectorAll('.data-table tbody tr');
    tableRows.forEach((row, index) => {
        row.style.animationDelay = `${index * 0.05}s`;
        row.classList.add('animate-fadeIn');
    });

    // Add focus animations to form inputs
    const formInputs = document.querySelectorAll('.form-input, .form-select, .form-textarea');
    formInputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('animate-pulse');
        });
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('animate-pulse');
        });
    });

    // Add click animation to cards
    const clickableCards = document.querySelectorAll('.stat-card, .feature-card');
    clickableCards.forEach(card => {
        card.addEventListener('click', function() {
            this.style.animation = 'none';
            setTimeout(() => {
                this.style.animation = '';
                this.classList.add('animate-pulse');
                setTimeout(() => this.classList.remove('animate-pulse'), 1000);
            }, 10);
        });
    });
});

// Animate numbers counting up
function animateValue(element, start, end, duration) {
    if (start === end) return;
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current);
    }, 16);
}

// Setup scroll-triggered animations
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-slideUp');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements that should animate on scroll
    const animateOnScroll = document.querySelectorAll('.form-section, .table-container, .chart-card, .info-section');
    animateOnScroll.forEach(el => observer.observe(el));
}

// Utility function for API calls
async function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const mergedOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(url, mergedOptions);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
}

// Confirm delete action
function confirmDelete(modelName) {
    return confirm(`Are you sure you want to delete "${modelName}"?`);
}

// Format date
function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

// Format percentage
function formatPercent(value) {
    if (value === null || value === undefined) return 'N/A';
    return (value * 100).toFixed(1) + '%';
}

