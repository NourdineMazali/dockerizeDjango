removeRedundantProfileButton();
removeUnnecessaryButton();
addEyeToSeeProfile();
changeHeaders();

function removeRedundantProfileButton() {
  $('.user-panel.mt-3.pb-3.mb-3.d-flex').remove();
}

function changeHeaders() {
  $search_form = $('#changelist-search');
  if ($search_form.length > 0) {
    $header = $('.card-header .card-title');
    $content = $('.card-tools.form-inline');
    customizeHeader($header);
    hideContent($content);
    manageToggle($header, $content);
  }
}

function addEyeToSeeProfile(){
  $('.dropdown-item.dropdown-footer').prepend('<i class="fas fa-eye"></i>');
}

function removeUnnecessaryButton() {
  $('.btn.btn-sm.btn-outline-info.btn-flat.changelink').remove();
}

function customizeHeader(header){
  header.append('<i class="fas fa-chevron-right rotate"></i>');
  header.css('cursor', 'pointer');
}

function hideContent(content) {
  content.toggle(15);
}

function manageToggle(header, content) {
  header.click(function () {
    $icon = $('.fas.fa-chevron-right.rotate');
    $icon.toggleClass("down");
    content.slideToggle(500);
  });
}
