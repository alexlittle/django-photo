
$(document).on('click', '[data-toggle="lightbox"]', function(event) {
  event.preventDefault();
  $(this).ekkoLightbox();
});

function selectall(){
  $(':checkbox').prop('checked', true);
}

function selectnone(){
  $(':checkbox').prop('checked', false);
}