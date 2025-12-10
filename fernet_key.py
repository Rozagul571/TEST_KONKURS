import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()


async def test_run_bot(bot_id: int):
    """Botni ishga tushirishni test qilish"""
    fastapi_url = os.getenv("FASTAPI_URL", "http://localhost:8001")

    print(f"🚀 Bot {bot_id} ni ishga tushirish testi...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{fastapi_url}/api/bots/run/{bot_id}")

            print(f"📊 Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Muvaffaqiyatli!")
                print(f"🤖 Bot: {data.get('bot_username')}")
                print(f"🔗 Webhook: {data.get('webhook')}")
            else:
                print(f"❌ Xato!")
                try:
                    error_data = response.json()
                    print(f"📋 Xato tafsiloti: {error_data}")
                except:
                    print(f"📋 Xato matni: {response.text}")

    except Exception as e:
        print(f"💥 Exception: {e}")


if __name__ == "__main__":
    # Test qilish uchun bot ID ni kiriting
    bot_id = input("Bot ID ni kiriting: ").strip()
    if bot_id.isdigit():
        asyncio.run(test_run_bot(int(bot_id)))
    else:
        print("❌ Noto'g'ri Bot ID")