#  bots/user_bots/base_template/services/channel_service.py:
"""
High-performance channel service with parallel checking
"""
import logging
import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from aiogram import Bot
from asgiref.sync import sync_to_async

from shared.redis_client import redis_client
from shared.utils import PerformanceTimer

logger = logging.getLogger(__name__)


class ChannelService:
    """Channel service with parallel checking and caching"""

    def __init__(self, competition_settings: Dict[str, Any]):
        self.competition_settings = competition_settings
        self.channels = competition_settings.get('channels', [])
        self.cache_ttl = 15  # 15 seconds cache

    async def check_user_channels(self, user_id: int, bot: Bot) -> Dict[str, Any]:
        """
        Check user's channel subscriptions with parallel processing
        """
        with PerformanceTimer(f"Channel check for user {user_id}"):
            # Try cache first
            cached_result = await self._get_cached_result(user_id)
            if cached_result:
                logger.debug(f"Cache hit for user {user_id} channel check")
                return cached_result

            # Parallel channel checking
            tasks = []
            for channel in self.channels:
                task = self._check_single_channel(channel, user_id, bot)
                tasks.append(task)

            # Run all checks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            result = self._process_check_results(results)

            # Cache the result
            await self._cache_result(user_id, result)

            return result

    async def _check_single_channel(self, channel: Dict[str, Any], user_id: int, bot: Bot) -> Dict[str, Any]:
        """Check single channel membership"""
        try:
            channel_username = channel.get('channel_username', '').strip()
            if not channel_username:
                return {
                    'channel': channel,
                    'status': 'error',
                    'error': 'Empty username'
                }

            # Remove @ if present
            if channel_username.startswith('@'):
                channel_username = channel_username[1:]

            # Check membership
            try:
                member = await bot.get_chat_member(f"@{channel_username}", user_id)

                status_map = {
                    'member': 'joined',
                    'administrator': 'joined',
                    'creator': 'joined',
                    'left': 'not_joined',
                    'restricted': 'request_needed',
                    'kicked': 'banned'
                }

                status = status_map.get(member.status, 'unknown')

                return {
                    'channel': channel,
                    'status': status,
                    'member_status': member.status,
                    'username': channel_username
                }

            except Exception as e:
                logger.warning(f"Channel check error for @{channel_username}: {e}")
                return {
                    'channel': channel,
                    'status': 'error',
                    'error': str(e),
                    'username': channel_username
                }

        except Exception as e:
            logger.error(f"Single channel check error: {e}")
            return {
                'channel': channel,
                'status': 'error',
                'error': str(e)
            }

    def _process_check_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process channel check results"""
        not_joined = []
        request_needed = []
        errors = []
        joined_count = 0

        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
                continue

            status = result.get('status')
            channel = result.get('channel', {})

            if status == 'joined':
                joined_count += 1
            elif status == 'not_joined':
                not_joined.append({
                    **channel,
                    'status': 'not_joined',
                    'username': result.get('username', '')
                })
            elif status == 'request_needed':
                request_needed.append({
                    **channel,
                    'status': 'request_needed',
                    'username': result.get('username', '')
                })
            elif status == 'error':
                errors.append(result.get('error', 'Unknown error'))

        total_channels = len(self.channels)
        all_joined = (joined_count == total_channels and
                     len(not_joined) == 0 and
                     len(request_needed) == 0)

        return {
            'all_joined': all_joined,
            'not_joined': not_joined,
            'request_needed': request_needed,
            'joined_channels': joined_count,
            'total_channels': total_channels,
            'errors': errors,
            'percentage': (joined_count / total_channels * 100) if total_channels > 0 else 0
        }

    async def _get_cached_result(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached channel check result"""
        try:
            if not redis_client.is_connected():
                return None

            bot_id = self.competition_settings.get('bot_id')
            if not bot_id:
                return None

            key = f"channel_check:{bot_id}:{user_id}"
            data = await redis_client.get_user_state(bot_id, user_id)

            if data and 'channel_check' in data:
                return data['channel_check']

        except Exception as e:
            logger.error(f"Get cached result error: {e}")

        return None

    async def _cache_result(self, user_id: int, result: Dict[str, Any]):
        """Cache channel check result"""
        try:
            if not redis_client.is_connected():
                return

            bot_id = self.competition_settings.get('bot_id')
            if not bot_id:
                return

            key = f"channel_check:{bot_id}:{user_id}"
            await redis_client.set_user_state(
                bot_id, user_id,
                {'channel_check': result},
                self.cache_ttl
            )

        except Exception as e:
            logger.error(f"Cache result error: {e}")

    async def get_channel_buttons(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare channel buttons for keyboard"""
        buttons = []

        for channel in channels:
            username = channel.get('username', channel.get('channel_username', ''))
            if not username:
                continue

            # Remove @ if present
            if username.startswith('@'):
                username = username[1:]

            channel_name = channel.get('channel_name', f"@{username}")

            # Determine button text based on status
            status = channel.get('status', '')
            if status == 'request_needed':
                button_text = f"📨 {channel_name} (Request)"
            else:
                button_text = f"📢 {channel_name}"

            buttons.append({
                'text': button_text,
                'url': f"https://t.me/{username}",
                'status': status
            })

        return buttons

    async def validate_channel_access(self, bot: Bot, channel_username: str) -> bool:
        """Validate bot has access to channel"""
        try:
            if channel_username.startswith('@'):
                channel_username = channel_username[1:]

            # Try to get chat info
            chat = await bot.get_chat(f"@{channel_username}")

            # Check if bot is admin or can see members
            try:
                bot_member = await bot.get_chat_member(f"@{channel_username}", (await bot.get_me()).id)
                return bot_member.status in ['administrator', 'creator']
            except:
                # If bot is not admin, check if we can at least see members
                return True

        except Exception as e:
            logger.error(f"Validate channel access error: {e}")
            return False

    async def batch_check_users(self, bot: Bot, user_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Batch check multiple users (for performance)"""
        results = {}

        # Create tasks for all users
        tasks = []
        for user_id in user_ids:
            task = self.check_user_channels(user_id, bot)
            tasks.append((user_id, task))

        # Run all tasks
        for user_id, task in tasks:
            try:
                result = await task
                results[user_id] = result
            except Exception as e:
                logger.error(f"Batch check error for user {user_id}: {e}")
                results[user_id] = {
                    'all_joined': False,
                    'error': str(e)
                }

        return results