import easyocr
import os

pic_dir = r"f:\yujun\github_file\EZlearn_in_ZJU\EE_lab\Report\10th\Q_pic"
out_dir = os.path.join(pic_dir, "ocr_results")
os.makedirs(out_dir, exist_ok=True)

reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

for fname in sorted(os.listdir(pic_dir)):
    if fname.endswith('.jpg'):
        fpath = os.path.join(pic_dir, fname)
        print(f"\n=== OCR: {fname} ===")
        results = reader.readtext(fpath, detail=0)
        text = '\n'.join(results)
        print(text)
        out_path = os.path.join(out_dir, fname.replace('.jpg', '.txt'))
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)

print("\n=== DONE ===")
