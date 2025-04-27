(function() {
    function initializePlayer() {
        // url: From CDN Server to Get Video
        var url = "https://dash.akamaized.net/akamai/bbb_30fps/bbb_30fps.mpd";
        var videoElement = document.querySelector('#videoPlayer');
        var player = dashjs.MediaPlayer().create();

        // Buffer Settings
        player.updateSettings({
            streaming: {
                buffer: {
                    // Buffer Prefetch Settings
                    bufferTimeAtTopQuality: 12,
                    bufferTimeAtTopQualityLongForm: 12,
                    bufferTimeDefault: 12,
                    longFormContentDurationThreshold: 600,
                    // Buffer Backward Settings
                    bufferPruningInterval: 1,
                    bufferToKeep: 60,
                }
            }
        });

        // Init Player
        player.initialize(videoElement, url, true);
        
        // Init ControlBar
        var controlbar = new ControlBar(player);
        controlbar.initialize();
        
        // Detect Browser
        detectBrowser();
        
        // Start Metrics Monitoring
        startMetricsMonitoring(player, videoElement);
        
        // Setup Event Handlers (in Sequence)
        setupEventHandlers(player);
        
        // Set Player to Global
        // This is to make sure that the player instance is accessible globally
        window.player = player;
    }

    // Waiting for DOM to be fully loaded, then init player
    document.addEventListener('DOMContentLoaded', initializePlayer); 
    /* 
    1. DOM: Document Object Model (interface for HTML and XML documents)
    2. DOMContentLoaded: All HTML has been loaded and parsed
    */
})();