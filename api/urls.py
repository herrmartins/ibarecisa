from django.urls import path
from . import views

urlpatterns = [
    path("", views.getData, name="get-data"),
    path("<int:pk>", views.getDetailedData, name="get-detailed-data"), 
    path(
        "transactions",
        views.TransactionCatListAPIView.as_view(),
        name="get-transactions",
    ),
    path(
        "transactions/post",
        views.TransactionsCreateAPIView.as_view(),
        name="post-transaction",
    ),
    path("getbalance", views.getCurrentBalance, name="get-current-balance"),
    path(
        "api/transaction/<int:pk>/delete",
        views.DeleteTransaction.as_view(),
        name="delete-transaction",
    ),
    path("search", views.unifiedSearch, name="secretarial-search"),
    path("mention-users", views.getMentionUsers, name="mention-users"),
]
