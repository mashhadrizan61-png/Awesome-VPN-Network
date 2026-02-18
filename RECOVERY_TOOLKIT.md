# Recovery Orchestrator (Experimental)

`recovery_orchestrator.py` یک ابزار ارکستریشن بازیابی اطلاعات برای سناریوهای پیچیده است:

- wiped / purged metadata
- fdisk repartition
- quick/full format
- partial/heavy overwrite
- SSD/NVMe with TRIM awareness
- encrypted volumes

## Reality check

اگر سکتور **واقعاً overwrite شده باشد**، در عمل بازیابی آن با نرم‌افزارهای معمولی تقریباً غیرممکن است.
این ابزار تضمین بازیابی نمی‌دهد و فقط بهترین مسیرهای forensic-safe را پیشنهاد می‌کند.

## Quick start

```bash
python3 recovery_orchestrator.py report --limit 20
```

## Create forensic image first (recommended)

> Important: روی دیسک اصلی عملیات نوشتن انجام ندهید.

```bash
sudo python3 recovery_orchestrator.py image --device /dev/sdX --out /cases/disk.img
```

## Output

گزارش JSON شامل:
- ابزارهای نصب‌شده (`ddrescue`, `testdisk`, `photorec`, ...)
- تعداد کل فضای سناریوهای پشتیبانی‌شده
- لیست سناریو + اکشن‌های پیشنهادی
