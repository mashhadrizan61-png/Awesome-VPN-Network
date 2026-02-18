# Awesome VPN Network - Virtual Modem Lab

این مخزن حالا یک ابزار ساده‌ی خط فرمان دارد برای ساخت یک **آزمایشگاه مودم مجازی** که به شما کمک می‌کند:

- پروفایل VPS ذخیره کنید
- پروفایل VPN ذخیره کنید
- وضعیت آمادگی آزمایشگاه را بررسی کنید
- قالب اولیه‌ی WireGuard بسازید

> ⚠️ این پروژه فقط برای استفاده‌ی آموزشی/آزمایشگاهی است. رعایت قوانین محلی و قوانین سرویس‌دهنده‌ها کاملاً بر عهده‌ی کاربر است.

## اجرا

نیازمندی: Python 3.10+

```bash
python3 virtual_modem.py --help
```

## مثال‌ها

### افزودن VPS
```bash
python3 virtual_modem.py add-vps \
  --name iran-exit-1 \
  --host 203.0.113.10 \
  --region eu-west \
  --ssh-port 22
```

### افزودن VPN
```bash
python3 virtual_modem.py add-vpn \
  --name wg-main \
  --protocol wireguard \
  --endpoint vpn.example.com \
  --port 51820
```

### لیست تنظیمات
```bash
python3 virtual_modem.py list
```

### گزارش مودم مجازی
```bash
python3 virtual_modem.py simulate-modem
```

### تولید قالب WireGuard
```bash
python3 virtual_modem.py wg-template \
  --client-private-key CLIENT_PRIVATE_KEY \
  --server-public-key SERVER_PUBLIC_KEY \
  --server-endpoint vpn.example.com \
  --server-port 51820
```

## فایل خروجی

پس از افزودن پروفایل‌ها، داده‌ها در فایل زیر ذخیره می‌شوند:

- `lab_profiles.json`
