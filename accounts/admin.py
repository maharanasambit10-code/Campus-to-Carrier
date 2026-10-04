from django.contrib import admin
from .models import Membership, Payment, SystemSetting, User


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'currency', 'status', 'razorpay_order_id', 'razorpay_payment_id', 'created_at')
    list_filter = ('status', 'plan', 'currency')
    search_fields = ('user__username', 'user__email', 'razorpay_order_id', 'razorpay_payment_id')
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(User)
admin.site.register(Membership)
admin.site.register(SystemSetting)