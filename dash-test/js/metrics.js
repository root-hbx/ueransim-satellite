// Detect browser type and show related information
function detectBrowser() {
    const userAgent = navigator.userAgent;
    let browserName = "Unknown";
    let metricsInfo = "";
    
    if (userAgent.indexOf("Chrome") > -1) {
        browserName = "Chrome";
        metricsInfo = "All Five Metrics will be shown, details can be checked in console";
    } else if (userAgent.indexOf("Safari") > -1) {
        browserName = "Safari";
        metricsInfo = "All Five Metrics will be shown, details can be checked in console";
    } else if (userAgent.indexOf("Firefox") > -1) {
        browserName = "Firefox";
        metricsInfo = "Only Four Metrics will be shown, details can be checked in console";
    } else if (userAgent.indexOf("MSIE") > -1 || userAgent.indexOf("Trident") > -1) {
        browserName = "Internet Explorer";
        metricsInfo = "Out of Date, please use Chrome / Safari / Edge ...";
    } else if (userAgent.indexOf("Edge") > -1) {
        browserName = "Edge";
        metricsInfo = "All Five Metrics will be shown, details can be checked in console";
    } else {
        browserName = "Unknown";
        metricsInfo = "Please use Chrome / Safari / Edge ...";
    }

    document.getElementById('browserType').innerText = browserName + (metricsInfo ? " - " + metricsInfo : "");
    return browserName;
}

/*
TL;DR Metrics on different browsers

(1) For Test on Chrome:

1. Reported BitRate
2. Buffer Level
3. Calculated BitRate
4. FrameRate
5. Resolution

(2) For Test on Firefox:

1. Reported BitRate
2. Buffer Level
3. FrameRate
4. Resolution
*/

/**
 * Start metrics monitoring
 * @param {Object} player - dash.js player instance
 * @param {HTMLElement} videoElement - video element
 */
function startMetricsMonitoring(player, videoElement) {
    let eventPoller = null;
    let bitrateCalculator = null;
    
    // Metrics Polling
    /*
    The four following metrics are polled from DASH.js:
    1. Reported Bitrate: The bitrate reported by the DASH.js player.
    2. Buffer Level: The current buffer level in seconds.
    3. Frame Rate: The frame rate of current video.
    4. Resolution: The resolution of current video.
    */
    eventPoller = setInterval(function () {
        var streamInfo = player.getActiveStream()?.getStreamInfo();
        var dashMetrics = player.getDashMetrics();
        var dashAdapter = player.getDashAdapter();

        if (dashMetrics && streamInfo) {
            // Get metrics directly from dash.js
            const periodIdx = streamInfo.index;
            var repSwitch = dashMetrics.getCurrentRepresentationSwitch('video');
            var bufferLevel = dashMetrics.getCurrentBufferLevel('video');
            var bitrate = repSwitch ? Math.round(dashAdapter.getBandwidthForRepresentation(repSwitch.to, periodIdx) / 1000) : NaN;
            var currentRep = player.getCurrentRepresentationForType('video');
            var frameRate = currentRep?.frameRate || '--';
            var resolution = currentRep ? (currentRep.width + 'x' + currentRep.height) : '--';
            
            document.getElementById('bufferLevel').innerText = bufferLevel + " s";
            document.getElementById('framerate').innerText = frameRate + " fps";
            document.getElementById('reportedBitrate').innerText = bitrate + " Kbps";
            document.getElementById('resolution').innerText = resolution;
        }
    }, 1000);

    // Calculated Bitrate
    /*
    1. webkitVideoDecodedByteCount is a non-standard API, only supported in Chrome / Safari / Edge
    2. It is not supported in Firefox / Zen
    */
    videoElement.addEventListener('loadeddata', function() {
        if (videoElement.webkitVideoDecodedByteCount !== undefined) {
            // Chrome / Safari / Edge支持
            var lastDecodedByteCount = 0;
            const bitrateInterval = 5;
            bitrateCalculator = setInterval(function () {
                try {
                    var currentDecodedByteCount = videoElement.webkitVideoDecodedByteCount;
                    if (typeof currentDecodedByteCount === 'number') {
                        var calculatedBitrate = (((currentDecodedByteCount - lastDecodedByteCount) / 1000) * 8) / bitrateInterval;
                        document.getElementById('calculatedBitrate').innerText = Math.round(calculatedBitrate) + " Kbps";
                        lastDecodedByteCount = currentDecodedByteCount;
                        console.log('[Valid Decoded]');
                        console.log('Bytes Decoded:', currentDecodedByteCount, 'BitRate:', Math.round(calculatedBitrate));
                    } else {
                        console.log('[Invalid Decoding]');
                        console.log('Invalid Decoded:', currentDecodedByteCount);
                    }
                } catch (e) {
                    console.error('Error when Decoding:', e);
                }
            }, bitrateInterval * 1000);
            console.log('Decoded Bytes:', lastDecodedByteCount);
        } else {
            document.getElementById('chrome-only').style.display = "none";
            console.log('Current Web Browser did not support webkitVideoDecodedByteCount API');
            console.log('Current Web Browser:', navigator.userAgent);
            console.log('Please use Chrome / Safari / Edge ... ');
        }
    });

    // Clear intervals when playback ends
    player.on(dashjs.MediaPlayer.events["PLAYBACK_ENDED"], function () {
        clearInterval(eventPoller);
        clearInterval(bitrateCalculator);
    });

    return { eventPoller, bitrateCalculator };
}