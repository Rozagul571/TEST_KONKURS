// django_app/static/admin/js/prize_type_toggle.js

(function($) {
    'use strict';

    function togglePrizeFields() {
        // Inline formsets uchun
        $('select[name$="-type"]').each(function() {
            var $select = $(this);
            var $row = $select.closest('tr');
            var type = $select.val();

            // Prize amount va description cells
            var $amountInput = $row.find('input[name$="-prize_amount"]');
            var $descInput = $row.find('input[name$="-description"], textarea[name$="-description"]');

            if (type === 'text') {
                // Text type - description ko'rinadi, amount yashirinadi
                $amountInput.closest('td').hide();
                $descInput.closest('td').show();
                $amountInput.val('');  // Clear amount
            } else {
                // Number type - amount ko'rinadi, description yashirinadi
                $amountInput.closest('td').show();
                $descInput.closest('td').hide();
                $descInput.val('');  // Clear description
            }
        });

        // Change form (edit page) uchun
        $('#id_type').each(function() {
            var type = $(this).val();
            var $amountField = $('.field-prize_amount');
            var $descField = $('.field-description');

            if (type === 'text') {
                $amountField.hide();
                $descField.show();
            } else {
                $amountField.show();
                $descField.hide();
            }
        });
    }

    $(document).ready(function() {
        // Initial toggle
        togglePrizeFields();

        // Type o'zgarganda
        $(document).on('change', 'select[name$="-type"], #id_type', function() {
            togglePrizeFields();
        });

        // Yangi inline qo'shilganda
        $(document).on('formset:added', function(event, $row, formsetName) {
            if (formsetName.indexOf('prize') !== -1) {
                togglePrizeFields();
            }
        });
    });

})(django.jQuery || jQuery);