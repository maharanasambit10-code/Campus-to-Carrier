
document.addEventListener("DOMContentLoaded", function() {
    document.body.classList.add('page-loaded');
    console.log("CAMPUSLINK Core loaded.");

    const dashboardDateEl = document.getElementById('live-dashboard-date');
    const dashboardTimeEl = document.getElementById('live-dashboard-time');
    const dashboardGreetingEl = document.getElementById('dashboard-greeting');
    const dashboardLastUpdateEl = document.getElementById('dashboard-last-update');

    if (dashboardDateEl && dashboardTimeEl) {
        const updateDashboardClock = () => {
            const now = new Date();
            const hour = now.getHours();
            let greeting = 'Good morning';
            if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
            else if (hour >= 17 || hour < 5) greeting = 'Good evening';
            if (dashboardGreetingEl) dashboardGreetingEl.textContent = greeting;
            dashboardDateEl.textContent = new Intl.DateTimeFormat('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
                year: 'numeric'
            }).format(now);
            dashboardTimeEl.textContent = new Intl.DateTimeFormat('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                second: '2-digit'
            }).format(now);
            if (dashboardLastUpdateEl) {
                dashboardLastUpdateEl.innerHTML = '<span class="status-pulse"></span>Updated just now';
            }
        };

        updateDashboardClock();
        setInterval(updateDashboardClock, 1000);
    }

    // Default theme is the premium blue-white combination ('light')
    let storedTheme = localStorage.getItem('campuslink-theme-v2');
    if (!storedTheme) {
        // Clear previous forced dark mode and default cleanly to light
        storedTheme = 'light';
        localStorage.setItem('campuslink-theme-v2', 'light');
    }
    const theme = storedTheme === 'dark' ? 'dark' : 'light';

    const themeToggles = document.querySelectorAll('.theme-toggle');
    const applyTheme = (mode) => {
        document.body.setAttribute('data-theme', mode);
        localStorage.setItem('campuslink-theme-v2', mode);
        themeToggles.forEach((toggle) => {
            const isDark = mode === 'dark';
            toggle.setAttribute('aria-pressed', String(isDark));
            toggle.classList.toggle('is-dark', isDark);
        });
    };

    applyTheme(theme);

    themeToggles.forEach((toggle) => {
        toggle.addEventListener('click', () => {
            const currentTheme = document.body.getAttribute('data-theme') || 'light';
            const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(nextTheme);
        });
    });

    const hero = document.querySelector('.premium-hero');
    if (hero) {
        const particleCount = 12;
        for (let i = 0; i < particleCount; i += 1) {
            const dot = document.createElement('span');
            dot.className = 'hero-particle';
            dot.style.left = `${Math.random() * 100}%`;
            dot.style.top = `${Math.random() * 100}%`;
            dot.style.animationDelay = `${(i * 0.45).toFixed(2)}s`;
            dot.style.setProperty('--size', `${(Math.random() * 10 + 6).toFixed(0)}px`);
            dot.style.setProperty('--duration', `${(Math.random() * 8 + 6).toFixed(0)}s`);
            hero.appendChild(dot);
        }
    }

    const showFieldError = (field, message) => {
        const wrapper = field.closest('.field-wrapper');
        if (!wrapper) return;

        const errorElement = wrapper.querySelector('.field-error') || document.createElement('div');
        errorElement.className = 'field-error show';
        errorElement.textContent = message;
        wrapper.appendChild(errorElement);
        field.classList.add('is-invalid');
        field.setAttribute('aria-invalid', 'true');
    };

    const clearFieldError = (field) => {
        const wrapper = field.closest('.field-wrapper');
        if (!wrapper) return;
        const errorElement = wrapper.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
        field.classList.remove('is-invalid');
        field.setAttribute('aria-invalid', 'false');
    };

    document.querySelectorAll('.auth-form').forEach((form) => {
        form.addEventListener('submit', (event) => {
            let isValid = true;

            form.querySelectorAll('input[required]').forEach((field) => {
                const value = field.value.trim();
                if (!value) {
                    isValid = false;
                    event.preventDefault();
                    showFieldError(field, 'Please fill out this field.');
                    if (!field.dataset.touched) {
                        field.focus();
                    }
                }
            });

            if (!isValid) {
                const firstInvalid = form.querySelector('input[required].is-invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
        });

        form.querySelectorAll('input[required]').forEach((field) => {
            field.addEventListener('input', () => {
                clearFieldError(field);
            });
            field.addEventListener('blur', () => {
                if (!field.value.trim()) {
                    showFieldError(field, 'Please fill out this field.');
                } else {
                    clearFieldError(field);
                }
            });
            field.addEventListener('invalid', (event) => {
                event.preventDefault();
                showFieldError(field, 'Please fill out this field.');
            });
        });
    });

    const registrationCta = document.querySelector('[data-registration-cta]');
    const applicationsHeading = document.querySelector('.applications-page .marketplace-heading');
    if (registrationCta && applicationsHeading) {
        const findOpportunities = applicationsHeading.querySelector(':scope > a');
        const actionGroup = document.createElement('div');
        actionGroup.className = 'application-heading-actions';
        if (findOpportunities) {
            findOpportunities.replaceWith(actionGroup);
            actionGroup.append(registrationCta, findOpportunities);
        } else {
            applicationsHeading.append(actionGroup);
            actionGroup.append(registrationCta);
        }
    }
    
    // Add a restrained stagger to repeated UI cards.
    const cards = document.querySelectorAll('.card, .feature-card, .public-stat');
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.classList.add('animate-fade-in');
            card.style.animationDelay = `${index * 0.06}s`;
        });
    }

    const revealItems = document.querySelectorAll('.landing-section, .steps-section, .copilot-section, .testimonial-section, .cta-section');
    if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.12 });
        revealItems.forEach((item) => {
            item.classList.add('scroll-reveal');
            revealObserver.observe(item);
        });
    }

    // Sidebar Active State Toggle
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.forEach(n => n.classList.remove('active', 'text-primary'));
            this.classList.add('active', 'text-primary');
        });
    });

    // Optional Chart.js Initialization if canvas exists
    const placementCanvas = document.getElementById('placementChart');
    if (placementCanvas && window.Chart) {
        const ctx = placementCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Technical Skills', 'Aptitude', 'Communication', 'Projects'],
                datasets: [{
                    data: [85, 90, 75, 95],
                    backgroundColor: ['#4f46e5', '#10b981', '#f59e0b', '#ef4444'],
                    borderWidth: 0
                }]
            },
            options: { cutout: '75%', responsive: true, plugins: { legend: { position: 'bottom' } } }
        });
    }
});
