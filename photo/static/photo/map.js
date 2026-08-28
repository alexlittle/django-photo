function initPhotoMap(dataElementId, labels) {
  var markers = JSON.parse(document.getElementById(dataElementId).textContent);

  var photoMap = L.map('mapid').setView([62.60, 29.76], 3);

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(photoMap);

  markers.forEach(function (marker) {
    var popupHtml =
      '<b>' + marker.name + '</b><br>' +
      '<a href="' + marker.tag_url + '" target="_blank">' + labels.viewPhotos + ' (' + marker.photo_count + ')</a><br>' +
      '<a href="' + marker.admin_url + '" target="_blank">' + labels.editTag + '</a>';

    L.marker([marker.lat, marker.lng]).addTo(photoMap).bindPopup(popupHtml);
  });
}
