let map;
let infoWindows = [];
let currentMarkers = [];
let markerCluster; // Declare markerCluster variable
let debounceTimer; // Declare a timer variable

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: 47.61766669226759, lng: -122.25876904043497 },
        zoom: 8
    });

    // Wait for the tiles to load before executing further code
    google.maps.event.addListenerOnce(map, 'tilesloaded', function () {
        // Load initial divesites
        loadDivesites();

        // Add bounds_changed event listener to detect map movement
        map.addListener('bounds_changed', function () {
            // Use debounce to delay the execution of loadDivesites
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                // Load divesites within the updated bounds
                loadDivesites();
            }, 300); // Adjust the delay as needed (e.g., 500 milliseconds)
        });
    });
}

function loadDivesites() {
    // Get current map bounds
    const bounds = map.getBounds();
    const ne = bounds.getNorthEast();
    const sw = bounds.getSouthWest();

    // Remove old markers from the map
    removeMarkers();

    // Call Flask route to get dive site data within the bounds
    fetch(`/get_dive_sites?ne_lat=${ne.lat()}&ne_lng=${ne.lng()}&sw_lat=${sw.lat()}&sw_lng=${sw.lng()}`)
        .then(response => response.json())
        .then(data => {

            // Iterate through dive sites and add markers
            data.forEach(site => {
                const marker = new google.maps.Marker({
                    position: { lat: site.latitude, lng: site.longitude },
                    title: site.name
                });

                // Create InfoWindow content
                const contentString = `
                    <div>
                        <h4>${site.name}</h4>
                        <p><a href="/divesites/${site.id}">Choose this divesite</a></p>
                    </div>
                `;

                // Create InfoWindow
                const infoWindow = new google.maps.InfoWindow({
                    content: contentString
                });

                // Add click event listener to marker to open the InfoWindow
                marker.addListener('click', () => {
                    // Close all existing InfoWindows
                    infoWindows.forEach(infoWindow => {
                        infoWindow.close();
                    });
                    // Open the clicked marker's InfoWindow
                    infoWindow.open(map, marker);
                });

                // Store the InfoWindow in the array
                infoWindows.push(infoWindow);

                // Add the marker to the array of markers
                currentMarkers.push(marker);
            });

            // Remove the existing clusterer
            if (markerCluster) {
                markerCluster.clearMarkers();
            }

            // Create a new clusterer with the current markers
            markerCluster = new MarkerClusterer(map, currentMarkers, {
                imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m',
                maxZoom: 10  // Adjust as needed
            });
        });
}

// Function to remove old markers from the map
function removeMarkers() {
    currentMarkers.forEach(marker => {
        marker.setMap(null);
    });
    currentMarkers = [];
}
