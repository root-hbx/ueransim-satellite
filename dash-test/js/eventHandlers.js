/**
 * Statistics Bottom
 * @param {Object} player
 */
function setupStatsButton(player) {
    document.getElementById('statsBtn').onclick = function() {
        var statsDiv = document.getElementById('stats');
        if (statsDiv.style.display === 'none' || statsDiv.innerHTML === '') {
            var metrics = player.getMetricsFor('video');
            statsDiv.innerHTML = JSON.stringify(metrics, null, 2);
            statsDiv.style.display = 'block';
        } else {
            statsDiv.style.display = 'none';
        }
    };
}

/**
 * CoreNet Switch
 * @param {Object} player
 */
function setupSwitchButton(player) {
    document.getElementById('switchBtn').onclick = function() {
        player.setAutoSwitchQualityFor('video', false);
        setTimeout(function() {
            player.setAutoSwitchQualityFor('video', true);
            alert('CoreNet will be switching in 20 seconds :)');
        }, 2000);
    };
}

/**
 * Event Handlers
 * @param {Object} player
 */
function setupEventHandlers(player) {
    setupStatsButton(player);
    setupSwitchButton(player);
}