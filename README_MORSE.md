# Universal Morse Decoder

این ابزار یک دیکدر/انکدر همه‌منظوره کد مورس است که برای سناریوهای پیچیده طراحی شده است:

- دیکد حالت استاندارد (کاراکترها جدا با فاصله و کلمات با `/`)
- دیکد مقاوم در برابر خطا (Fuzzy) برای سیگنال‌های خراب یا ناقص
- دیکد جریان پیوسته بدون فاصله با الگوریتم Beam Search
- انکد متن به مورس
- خروجی JSON برای اتصال به سیستم‌های بزرگ‌تر

> نکته: «پشتیبانی از همه چیز» در عمل نامحدود نیست، اما این پیاده‌سازی برای پوشش طیف وسیعی از ورودی‌های واقعی و noisy طراحی شده است.

## اجرا

```bash
python3 universal_morse_decoder.py ".... . .-.. .-.. --- / .-- --- .-. .-.. -.."
python3 universal_morse_decoder.py "......-...-..---" --mode continuous --json
python3 universal_morse_decoder.py "HELLO WORLD" --mode encode
```

## تست

```bash
python3 -m unittest discover -s tests -v
```
