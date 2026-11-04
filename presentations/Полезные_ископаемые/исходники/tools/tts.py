import asyncio, ssl, os, sys, json
import edge_tts.communicate as c
c._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
import edge_tts
VOICE="ru-RU-SvetlanaNeural"
PH = json.load(open(sys.argv[1]))
out = sys.argv[2]
async def one(key, text, rate, pitch):
    com = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, proxy=os.environ.get("HTTPS_PROXY"))
    await com.save(os.path.join(out, key + ".mp3"))
async def main():
    for p in PH:
        await one(p["key"], p["text"], p.get("rate","+0%"), p.get("pitch","+8Hz"))
        print("ok", p["key"])
asyncio.run(main())
