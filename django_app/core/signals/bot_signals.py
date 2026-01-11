# from django.db.models.signals import post_save, pre_save
# from django.dispatch import receiver
# from asgiref.sync import async_to_sync
# import httpx
# import os
# from ..models.bot import BotSetUp, BotStatus
#
# @receiver(pre_save, sender=BotSetUp)
# def save_old_status(sender, instance, **kwargs):
#     try:
#         obj = sender.objects.get(pk=instance.pk)
#         instance._old_status = obj.status
#     except:
#         instance._old_status = None
#
# @receiver(post_save, sender=BotSetUp)
# def handle_bot_status_change(sender, instance, **kwargs):
#     if instance.status == BotStatus.RUNNING and getattr(instance, '_old_status', None) == BotStatus.PENDING:
#         async_to_sync(send_run_bot_request)(instance)
#     elif instance.status == BotStatus.STOPPED and getattr(instance, '_old_status', None) == BotStatus.RUNNING:
#         async_to_sync(send_stop_bot_request)(instance)
#
# async def send_run_bot_request(bot_setup):
#     fastapi_url = f"{os.getenv('FASTAPI_URL')}/api/bots/run/{bot_setup.id}"  # <--- TO‘G‘RILANDI
#     async with httpx.AsyncClient() as client:
#         await client.post(fastapi_url, timeout=30.0)
#
# async def send_stop_bot_request(bot_setup):
#     fastapi_url = f"{os.getenv('FASTAPI_URL')}/api/bots/stop/{bot_setup.id}"  # <--- TO‘G‘RILANDI
#     async with httpx.AsyncClient() as client:
#         await client.post(fastapi_url, timeout=30.0)  # DELETE emas, POST