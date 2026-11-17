from django.urls import path

from billing.views import (
    AcceptInvitationView,
    BillingView,
    InvitationListView,
    InvitationPreviewView,
    InviteView,
    PlansView,
    RegisterTenantView,
    SubscribeView,
)

urlpatterns = [
    path("plans", PlansView.as_view()),
    path("tenants/register", RegisterTenantView.as_view()),
    path("tenants/invitations", InvitationListView.as_view()),
    path("tenants/invite", InviteView.as_view()),
    path("invitations/accept", AcceptInvitationView.as_view()),
    path("invitations/<str:token>", InvitationPreviewView.as_view()),
    path("billing", BillingView.as_view()),
    path("billing/subscribe", SubscribeView.as_view()),
]
