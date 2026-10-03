from django.shortcuts import redirect

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. إذا كان الطلب يستهدف أي API (يبدأ بـ /api/) سيبه يمر عادي
        # لأن DRF هو اللي بيتولى التحقق من الـ Bearer Token والـ Permissions
        if request.path.startswith('/api/'):
            return self.get_response(request)

        # 2. قائمة المسارات الاستثنائية لصفحات الـ Web العادية
        exempt_urls = [
            '/admin/login/', # لوجن الأدمن
        ]

        # 3. تطبيق الحماية والـ Redirect لصفحات الـ Web فقط
        if not request.user.is_authenticated and request.path not in exempt_urls:
            return redirect('/admin/login/') # أو صفحة اللوجن الخاصة بالـ Web

        response = self.get_response(request)
        return response