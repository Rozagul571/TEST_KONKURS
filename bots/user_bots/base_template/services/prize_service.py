# bots/user_bots/base_template/services/prize_service.py
from asgiref.sync import sync_to_async

class PrizeService:
    """Prize servisi. Vazifasi: Sovrinlarni olish. Misol: get_prizes - list qaytaradi."""
    def __init__(self, competition_data):
        self.competition_data = competition_data

    @sync_to_async
    def get_prizes(self):
        return self.competition_data['prizes']