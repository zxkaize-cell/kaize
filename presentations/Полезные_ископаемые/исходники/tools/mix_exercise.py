import json, subprocess, os
S = os.path.dirname(os.path.abspath(__file__)) + "/.."
T = S + "/snd/tts_trim/"
MUSIC = S + "/snd/raw/music_1142.mp3"
beat, phase = 0.5, 0.302
def b(k): return round(phase + k*beat, 3)
def dur(f): return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
lines = ["Мы копаем глубоко —", "Достаём руду легко —", "Уголь, глину и песок", "Из земли берём мы в срок.", "Но природу охраняем,", "Землю нашу сохраняем!"]
moves = ["наклоны вперёд", "выпрямиться, руки вверх", "повороты вправо-влево", "приседания", "руки в стороны", "руки вверх"]
poses = [("P1","P0"),("P2","P0"),("P3","P3m"),("P4","P0"),("P5","P0"),("P6","P2")]
clips=[]; events=[]  # events: {t, line, pose}
clips.append(("intro", b(1)))
events.append({"t":0.0,"pose":"C1","line":-1,"caption":"Встаём и повторяем!"})
r1 = 14; s1 = 12
for i in range(6):
    st = r1 + i*s1
    clips.append((f"r1_{i+1}", b(st)))
    for k in range(0, s1, 2):
        events.append({"t":b(st+k),"pose":poses[i][(k//2)%2],"line":i,"round":1})
ag = r1 + 6*s1
clips.append(("again", b(ag+1)))
events.append({"t":b(ag),"pose":"C4","line":-1,"caption":"Ещё разок — быстрее!"})
r2 = ag + 10; s2 = 8
for i in range(6):
    st = r2 + i*s2
    clips.append((f"r2_{i+1}", b(st)))
    for k in range(0, s2, 2):
        events.append({"t":b(st+k),"pose":poses[i][(k//2)%2],"line":i,"round":2})
end = r2 + 6*s2
clips.append(("outro", b(end+1)))
events.append({"t":b(end),"pose":"C4","line":-1,"caption":"Молодцы!"})
outro_end = b(end+1) + dur(T+"outro.wav")
total = round(outro_end + 3.0, 2)
# build ffmpeg
inputs=['-i',MUSIC]; fl=[]
for idx,(k,t) in enumerate(clips):
    inputs += ['-i', T+k+'.wav']
    ms=int(t*1000)
    fl.append(f"[{idx+1}:a]aresample=44100,pan=stereo|c0=c0|c1=c0,adelay={ms}|{ms},volume=1.0[v{idx}]")
vin=''.join(f"[v{i}]" for i in range(len(clips)))
fl.append(f"{vin}amix=inputs={len(clips)}:normalize=0:dropout_transition=0,apad=whole_dur={total}[voice]")
fl.append("[voice]asplit=2[vsc][vmix]")
fl.append(f"[0:a]atrim=0:{total},asetpts=N/SR/TB,aresample=44100,volume=0.42,afade=t=in:st=0:d=0.6,afade=t=out:st={total-3.2}:d=3.2[mus]")
fl.append("[mus][vsc]sidechaincompress=threshold=0.02:ratio=8:attack=40:release=450:makeup=1[duck]")
fl.append("[duck][vmix]amix=inputs=2:normalize=0,alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11[out]")
out = S + "/build/fizminutka.mp3"
cmd=['ffmpeg','-v','error','-y',*inputs,'-filter_complex',';'.join(fl),'-map','[out]','-t',str(total),'-ar','44100','-b:a','160k',out]
subprocess.run(cmd,check=True)
json.dump({"total":total,"lines":lines,"moves":moves,"clips":clips,"events":events,"beat":beat}, open(S+"/build/fizminutka_timeline.json","w"), ensure_ascii=False, indent=1)
print("total", total, "events", len(events), "dur", dur(out))
