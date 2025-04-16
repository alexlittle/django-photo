

function selectall(){
  $(':checkbox').each(function() {
    $(this).prop('checked', true);
    $(this).closest('.photo-thumbnail-container').addClass('selected');
  });
}

function selectnone(){
   $(':checkbox').each(function() {
    $(this).prop('checked', false);
    $(this).closest('.photo-thumbnail-container').removeClass('selected');
  });
}

// for highlighting photo background when selected
$(document).ready(function() {
  // On page load, find all checked checkboxes and add the 'selected' class
  // to their closest '.photo-thumbnail-container' parent.
  $('input[type="checkbox"]:checked').each(function() {
    $(this).closest('.photo-thumbnail-container').addClass('selected');
  });

  // Click handler for toggling selection (same as before)
  $('.photo-image').on('click', function(event) {
    if ($(event.target).closest('a[data-toggle="lightbox"]').length) {
      return;
    }

    const $photoImage = $(this);
    const $container = $photoImage.closest('.photo-thumbnail-container');
    const $checkbox = $container.find('input[type="checkbox"]'); // Find the checkbox within the container

    if ($checkbox.length) {
      $checkbox.prop('checked', !$checkbox.prop('checked'));
      $container.toggleClass('selected', $checkbox.prop('checked'));
      $checkbox.trigger('change');
    }
  });
});
