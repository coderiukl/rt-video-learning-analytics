from django.contrib import admin

from .models import AuditLog, Certificate, CourseReview, Discussion, LearningGoal, Notification, Report, SystemSetting, Wishlist

admin.site.register(AuditLog)
admin.site.register(Notification)
admin.site.register(SystemSetting)
admin.site.register(Wishlist)
admin.site.register(CourseReview)
admin.site.register(Certificate)
admin.site.register(LearningGoal)
admin.site.register(Discussion)
admin.site.register(Report)

