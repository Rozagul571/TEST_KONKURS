# django_app/core/admin/prize_admin.py
"""
Prize Admin - O'zbekcha fieldlar va Type bo'yicha dynamic visibility
"""
from django.contrib import admin
from django import forms
from django.utils.html import format_html


class PrizeAdminForm(forms.ModelForm):
    """Prize form - Type bo'yicha field visibility"""

    class Meta:
        fields = '__all__'
        labels = {
            'place': "O'rin",
            'prize_name': "Sovg'a nomi",
            'prize_amount': "Pul miqdori (so'm)",
            'type': "Turi",
            'description': "Tavsif (text uchun)",
        }
        help_texts = {
            'place': "Nechanchi o'rin uchun sovg'a",
            'prize_name': "Sovg'a nomi (ixtiyoriy)",
            'prize_amount': "Pul mukofoti (faqat 'Pul' turi uchun)",
            'type': "'Pul' - pul mukofoti, 'Matn' - boshqa sovg'a",
            'description': "Sovg'a tavsifi (faqat 'Matn' turi uchun)",
        }

    class Media:
        js = ('admin/js/prize_type_toggle.js',)


class PrizeInline(admin.TabularInline):
    """Prize inline for Competition"""
    from django_app.core.models import Prize
    model = Prize
    form = PrizeAdminForm
    extra = 1
    ordering = ['place']

    # O'zbekcha fieldlar
    verbose_name = "Sovg'a"
    verbose_name_plural = "Sovg'alar"

    fields = ['place', 'prize_name', 'type', 'prize_amount', 'description']

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('place')


# JavaScript for dynamic field visibility
PRIZE_TYPE_TOGGLE_JS = """
(function($) {
    $(document).ready(function() {
        function togglePrizeFields() {
            $('.field-type select, select[name$="-type"]').each(function() {
                var $select = $(this);
                var $row = $select.closest('tr, .form-row');
                var type = $select.val();

                var $amountField = $row.find('.field-prize_amount, input[name$="-prize_amount"]').closest('td, .field-prize_amount');
                var $descField = $row.find('.field-description, input[name$="-description"], textarea[name$="-description"]').closest('td, .field-description');

                if (type === 'text') {
                    $amountField.hide();
                    $descField.show();
                } else {
                    $amountField.show();
                    $descField.hide();
                }
            });
        }

        // Initial toggle
        togglePrizeFields();

        // On change
        $(document).on('change', '.field-type select, select[name$="-type"]', togglePrizeFields);

        // On new inline added
        $(document).on('formset:added', togglePrizeFields);
    });
})(django.jQuery);
"""

# from django.contrib import admin
# from django.http import HttpRequest
# from ..models.prize import Prize
# from ..models.user import User
#
# @admin.register(Prize)
# class PrizeAdmin(admin.ModelAdmin):
#     list_display = ("competition_display", "place", "prize_name", "prize_amount")
#     def competition_display(self, obj):
#         return obj.competition.name if obj.competition else "-"
#     competition_display.short_description = "Konkurs"
#     def get_queryset(self, request: HttpRequest):
#         qs = super().get_queryset(request)
#         if request.user.is_superuser:
#             return qs
#         try:
#             telegram_id = int(request.user.username.split('_')[-1])
#             admin_user = User.objects.get(telegram_id=telegram_id)
#             return qs.filter(competition__creator=admin_user)
#         except:
#             return qs.none()
#     def has_module_permission(self, request):
#         return request.user.is_superuser or request.user.is_staff
#     def has_view_permission(self, request, obj=None):
#         if request.user.is_superuser:
#             return True
#         if obj is None:
#             return request.user.is_staff
#         try:
#             telegram_id = int(request.user.username.split('_')[-1])
#             admin_user = User.objects.get(telegram_id=telegram_id)
#             return obj.competition.creator == admin_user
#         except:
#             return False
#     def has_add_permission(self, request):
#         return request.user.is_superuser or request.user.is_staff
#     def has_change_permission(self, request, obj=None):
#         if request.user.is_superuser:
#             return True
#         if obj is None:
#             return request.user.is_staff
#         try:
#             telegram_id = int(request.user.username.split('_')[-1])
#             admin_user = User.objects.get(telegram_id=telegram_id)
#             return obj.competition.creator == admin_user
#         except:
#             return False
#     def has_delete_permission(self, request, obj=None):
#         return request.user.is_superuser