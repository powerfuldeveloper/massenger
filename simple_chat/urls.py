"""simple_chat URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include

from simple_chat.views import Login, Main, UserCreate, UserUpdate, ShowUsers, ShowMessage, ShowChats, StartChat, \
    ChatDetails, CreateMessage

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', Login.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/', include([
        path('', UserCreate.as_view(), name='user-page'),
        path('show/', ShowUsers.as_view(), name='user-show-endpoint'),
        path('update/<int:pk>', UserUpdate.as_view(), name='user-update-page'),
    ])),
    path('chats/', include([
        path('start/', StartChat.as_view(), name='chat-start-endpoint'),
        path('show/', ShowChats.as_view(), name='chat-show-endpoint'),
        path('detail/', ChatDetails.as_view(), name='chat-detail-endpoint'),
        # path('updates/', ChatUpdates.as_view(), name='chat-updates-endpoint'),
    ])),
    path('messages/', include([
        path('create/', CreateMessage.as_view(), name='message-create-endpoint'),
        path('show/', ShowMessage.as_view(), name='message-show-endpoint'),
    ])),
    path('', Main.as_view(), name='main-page'),
]
urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
