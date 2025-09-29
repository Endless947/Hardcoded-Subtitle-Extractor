from datetime import timedelta

def srt_time(seconds):
    td = timedelta(seconds=seconds)
    total_ms = int(td.total_seconds() * 1000)
    h = total_ms // 3600000
    m = (total_ms % 3600000) // 60000
    s = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def write_srt(subs, out_path="output.srt"):
    """
    subs: list of tuples (start_sec, end_sec, text)
    """
    with open(out_path, "w", encoding="utf-8") as f:
        for i, (st, en, text) in enumerate(subs, start=1):
            f.write(f"{i}\n")
            f.write(f"{srt_time(st)} --> {srt_time(en)}\n")
            f.write(f"{text}\n\n")
