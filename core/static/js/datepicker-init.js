function initDatePicker(el, opts) {
    var defaults = {
        dateFormat: 'd/m/Y',
        locale: 'pt',
        allowInput: true,
        disableMobile: true,
    };
    var config = Object.assign({}, defaults, opts || {});
    return flatpickr(el, config);
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.datepicker').forEach(function(el) {
        if (!el._flatpickr) {
            initDatePicker(el);
        }
    });
});
