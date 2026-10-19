import os, httpx, discord

TOKEN = os.environ["DISCORD_TOKEN"].strip()
API_KEY = os.environ["ANTHROPIC_API_KEY"].strip()
MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5")
SYSTEM = ("Sen foydali AI yordamchisan. Foydalanuvchi qaysi tilda yozsa, "
          "o'sha tilda (asosan o'zbekcha) javob ber. "
          "Kod so'ralsa, to'liq va ishlaydigan kod yoz.")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
history = {}

@client.event
async def on_ready():
    print("Bot ishga tushdi:", client.user)

@client.event
async def on_message(m):
    if m.author.bot:
        return
    is_dm = isinstance(m.channel, discord.DMChannel)
    if not (is_dm or client.user in m.mentions):
        return

    text = m.content
    for tag in (f"<@{client.user.id}>", f"<@!{client.user.id}>"):
        text = text.replace(tag, "")
    text = text.strip()
    if not text:
        await m.reply("Savolingni yoz.")
        return

    msgs = history.setdefault(m.author.id, [])
    msgs.append({"role": "user", "content": text})
    del msgs[:-20]
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)

    try:
        async with m.channel.typing():
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": API_KEY,
                             "anthropic-version": "2023-06-01",
                             "content-type": "application/json"},
                    json={"model": MODEL, "max_tokens": 2000,
                          "system": SYSTEM, "messages": msgs})
                if r.status_code != 200:
                    print("XATO:", r.status_code, r.text)
                    r.raise_for_status()
                answer = r.json()["content"][0]["text"]
    except Exception as e:
        msgs.pop()
        print("XATO:", repr(e))
        await m.reply("Xatolik yuz berdi, qayta urinib ko'r.")
        return

    msgs.append({"role": "assistant", "content": answer})
    for i in range(0, len(answer), 1900):
        await m.reply(answer[i:i+1900])

client.run(TOKEN)
