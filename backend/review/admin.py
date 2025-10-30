from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "comment", "rating", "user_id"]
    list_filter = ["id", "user_id"]

    def get_user_id(self, obj):
        return obj.user.id
