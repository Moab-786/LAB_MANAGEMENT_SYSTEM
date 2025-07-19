from django.contrib import admin
from .models import IssueRecord, ReturnRecord, Component, Student

@admin.register(IssueRecord)
class IssueRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'component', 'quantity_issued', 'date_issued', 'get_return_status')
    list_filter = ('returned', 'student', 'component')
    readonly_fields = ('date_issued',)  # Prevent editing

    def get_return_status(self, obj):
        return "✅ Returned" if obj.returned else "❌ Not Returned"
    get_return_status.short_description = 'Return Status'  # Column name in admin
    get_return_status.admin_order_field = 'returned'       # Allow sorting

@admin.register(ReturnRecord)
class ReturnRecordAdmin(admin.ModelAdmin):
    list_display = ('issue', 'get_quantity_returned', 'condition', 'date_returned')
    readonly_fields = ('date_returned',)  # Prevent editing

    def get_quantity_returned(self, obj):
        return obj.issue.quantity_issued
    get_quantity_returned.short_description = 'Quantity Returned'

admin.site.register(Component)
admin.site.register(Student)
