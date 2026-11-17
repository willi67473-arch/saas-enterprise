from django.shortcuts import get_object_or_404
from rest_framework.response import Response

from core.views import TenantAPIView
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class NotificationListView(TenantAPIView):
    def get(self, request):
        items = Notification.objects.filter(user=request.user).order_by("-id")[:30]
        return Response(NotificationSerializer(items, many=True).data)


class NotificationReadView(TenantAPIView):
    def patch(self, request, pk):
        # 404 si la notification n'est pas la sienne (ou n'est pas de son tenant)
        notification = get_object_or_404(Notification.objects.filter(user=request.user), pk=pk)
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllView(TenantAPIView):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": "Toutes les notifications sont lues."})
