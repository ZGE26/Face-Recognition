# Test Assets

Letakkan file gambar wajah di direktori ini untuk menjalankan test.

## File yang dibutuhkan

| File | Keterangan |
|---|---|
| `face1.jpg` | Foto wajah orang pertama — **wajib** untuk semua test |
| `face2.jpg` | Foto wajah orang **berbeda** — opsional, untuk test negatif |

## Aturan gambar

- Format: JPEG atau PNG
- `face1.jpg` harus mengandung **tepat satu wajah**
- `face2.jpg` harus orang yang **berbeda** dengan `face1.jpg`
- Kualitas cukup jelas (tidak blur, pencahayaan wajar)

## Menjalankan test

```bash
# Semua test
pytest tests/ -v

# Hanya register
pytest tests/test_register.py -v

# Hanya scan
pytest tests/test_scan.py -v
```

Test akan otomatis di-skip jika file gambar tidak ditemukan.
