import os

target = r'dist\CognitiveMaze\_internal'
entries = []
for item in os.listdir(target):
    full = os.path.join(target, item)
    if os.path.isdir(full):
        size = sum(os.path.getsize(os.path.join(dirpath, f)) for dirpath, _, filenames in os.walk(full) for f in filenames if os.path.exists(os.path.join(dirpath, f)))
    else:
        size = os.path.getsize(full)
    entries.append((item, size / (1024 * 1024)))

entries.sort(key=lambda x: x[1], reverse=True)
total_size = sum(e[1] for e in entries)
print(f"TOTAL _internal SIZE: {total_size:.2f} MB\n")
print(f"{'Item':<40} | {'Size (MB)':>10}")
print('-'*55)
for name, mb in entries[:30]:
    print(f"{name:<40} | {mb:>10.2f} MB")
