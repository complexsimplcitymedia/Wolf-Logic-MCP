// Wolf Memory Counter Widget - Space Theme
(function() {
    const API_URL = 'https://wolf-ui.complexsimplicityai.com/api/memories';

    // Create widget container
    const widget = document.createElement('div');
    widget.id = 'wolf-memory-widget';
    widget.innerHTML = `
        <style>
            #wolf-memory-widget {
                position: fixed;
                bottom: 2rem;
                left: 2rem;
                z-index: 50;
                font-family: ui-sans-serif, system-ui, sans-serif;
            }
            .wolf-widget-inner {
                background: rgba(0, 0, 0, 0.6);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 0.75rem;
                padding: 1rem 1.5rem;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 0.25rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            }
            .wolf-widget-inner:hover {
                border-color: rgba(168, 85, 247, 0.3);
                box-shadow: 0 0 30px rgba(168, 85, 247, 0.1);
            }
            .wolf-count {
                font-size: 2rem;
                font-weight: 700;
                background: linear-gradient(to right, #a855f7, #3b82f6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                line-height: 1;
            }
            .wolf-label {
                font-size: 0.65rem;
                color: rgba(255, 255, 255, 0.5);
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }
            .wolf-pulse {
                width: 6px;
                height: 6px;
                background: #a855f7;
                border-radius: 50%;
                animation: wolf-pulse 2s infinite;
                position: absolute;
                top: 0.75rem;
                right: 0.75rem;
            }
            @keyframes wolf-pulse {
                0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(168, 85, 247, 0.7); }
                50% { opacity: 0.5; box-shadow: 0 0 0 4px rgba(168, 85, 247, 0); }
            }
            @media (max-width: 640px) {
                #wolf-memory-widget {
                    bottom: 1rem;
                    left: 1rem;
                }
                .wolf-widget-inner {
                    padding: 0.75rem 1rem;
                }
                .wolf-count {
                    font-size: 1.5rem;
                }
            }
        </style>
        <div class="wolf-widget-inner" style="position: relative;">
            <div class="wolf-pulse"></div>
            <div class="wolf-count" id="wolf-memory-count">--</div>
            <div class="wolf-label">Memories</div>
        </div>
    `;

    document.body.appendChild(widget);

    function formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    async function updateCount() {
        try {
            const res = await fetch(API_URL);
            const data = await res.json();
            if (data.count) {
                document.getElementById('wolf-memory-count').textContent = formatNumber(data.count);
            }
        } catch (e) {
            console.log('Memory widget fetch error:', e);
        }
    }

    // Initial fetch and poll every 30 seconds
    updateCount();
    setInterval(updateCount, 30000);
})();
