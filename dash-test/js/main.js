(function() {
    function initializePlayer() {
        // url: From CDN Server to Get Video
        var url = "https://cmafref.akamaized.net/cmaf/live-ull/2006350/akambr/out.mpd";
        var videoElement = document.querySelector('#videoPlayer');
        var player = dashjs.MediaPlayer().create();

        // Buffer Settings
        player.updateSettings({
            streaming: {
                buffer: {
                    // Buffer Prefetch Settings
                    bufferTimeAtTopQuality: 10,
                    bufferTimeAtTopQualityLongForm: 10,
                    bufferTimeDefault: 10,
                    longFormContentDurationThreshold: 60,
                    // Buffer Backward Settings
                    bufferPruningInterval: 0.1,
                    bufferToKeep: 0.5,
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