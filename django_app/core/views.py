from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models.bot import BotSetUp
from .models.user import User

def panel_view(request, bot_id):
    """Panel view. O'ZGARTIRILGAN: bot_id bilan filter, faqat owner va active."""
    bot = get_object_or_404(BotSetUp, id=bot_id, is_active=True)
    telegram_id = int(request.user.username.split('_')[-1])
    if bot.owner.telegram_id != telegram_id:
        raise Http404("Ruxsat yo'q!")
    context = {'bot': bot, 'competition': bot.competition}
    return render(request, 'admin/core/competition/change_form.html', context)  #