from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import QuerySet, Q, Model
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView

from simple_chat.forms import UserCreationForm, UserUpdateForm, MessageCreationForm
from user.models import Message, Chat


class Login(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True


class Main(LoginRequiredMixin, TemplateView):
    template_name = 'pages/main/main.html'


class UserCreate(LoginRequiredMixin, CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('user-page')
    template_name = 'pages/users/users.html'
    model = get_user_model()

    def form_valid(self, form):
        res = super().form_valid(form)
        self.object.first_name = form.cleaned_data['first_name']
        self.object.last_name = form.cleaned_data['last_name']
        self.object.set_password(form.cleaned_data['password'])
        self.object.save()
        return res

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = get_user_model().objects.all()
        return context

    def get_success_url(self):
        messages.success(self.request, 'کاربر با موفقیت ایجاد شده')
        return super().get_success_url()


class UserUpdate(LoginRequiredMixin, UpdateView):
    form_class = UserUpdateForm
    success_url = reverse_lazy('user-page')
    template_name = 'pages/users/edit-users.html'
    model = get_user_model()

    def form_valid(self, form):
        res = super().form_valid(form)
        self.object.set_password(form.cleaned_data['password'])
        self.object.save()
        return res

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = get_user_model().objects.all()
        return context

    def get_success_url(self):
        messages.success(self.request, 'کاربر با موفقیت بروزرسانی شد')
        return super().get_success_url()


class BasicAttrsMixIn:
    page = 0
    per_page = 0
    data = None
    cu = None

    def parse_basics(self):
        self.cu = self.request.user

        if self.request.method.lower() == 'post':
            self.data = self.request.POST
        elif self.request.method.lower() == 'get':
            self.data = self.request.GET

        try:
            self.page = int(self.data.get('p', '1'))
        except:
            self.page = 1

        if self.page < 1:
            self.page = 1
        if self.per_page == 0:
            try:
                self.per_page = int(self.data.get('pp', '5'))
            except:
                self.per_page = 5


class PaginationMixIn(BasicAttrsMixIn):
    model = None
    qs = QuerySet()
    pg = []

    def dispatch(self, request, *args, **kwargs):
        validated = self.validate_data()
        if validated:
            return validated
        self.parse_basics()
        self.qs = self.model.objects.all()

        self.prepare_qs()

        self.pg = Paginator(self.qs, self.per_page)

        return self.prepare_response()

    def validate_data(self):
        return

    def prepare_qs(self):
        pass

    def to_dict(self, obj):
        return obj.to_dict()

    def prepare_data(self):
        response_data = []
        for data in self.pg.page(self.page).object_list:
            response_data.append(self.to_dict(data))
        return response_data

    def prepare_response(self):
        return JsonResponse({
            'ok': True,
            'data': self.prepare_data()
        }, safe=False)


class ShowUsers(LoginRequiredMixin, PaginationMixIn, View):
    model = get_user_model()

    def prepare_qs(self):
        self.qs = self.qs.exclude(id=self.cu.id)
        self.qs = self.qs.exclude(id__in=Chat.objects.filter(from_user=self.cu.id).values_list('to_user__id'))
        self.qs = self.qs.exclude(id__in=Chat.objects.filter(to_user=self.cu.id).values_list('from_user__id'))


class StartChat(LoginRequiredMixin, View):

    def post(self, request):
        try:
            requested_user = int(self.request.POST.get('ru'))
            requested_user = get_user_model().objects.get(pk=requested_user)
        except:
            return JsonResponse({'ok': False, 'messages': [
                'USER_DOES_NOT_EXISTS',
            ]})

        chat = Chat.objects.filter((Q(from_user=self.request.user) | Q(to_user=self.request.user)) & (
                Q(from_user=requested_user) | Q(to_user=requested_user))).first()
        if not chat:
            chat = Chat.objects.create(from_user=self.request.user, to_user=requested_user)

        return JsonResponse({
            'ok': True,
            'messages': [
                'CHAT_CREATED'
            ],
            'data': {
                'chat': chat.to_dict()
            }
        })


class ShowChats(LoginRequiredMixin, PaginationMixIn, View):
    model = Chat

    def prepare_qs(self):
        self.qs = self.qs.filter(Q(from_user=self.cu) | Q(to_user=self.cu))


class ChatDetails(LoginRequiredMixin, PaginationMixIn, View):
    model = Message
    chat = None
    older_than = None

    def prepare_qs(self):
        self.qs = self.qs.filter(chat=self.chat).order_by('-id')
        older_than = self.request.POST.get('older_than')
        if older_than:
            self.qs = self.qs.filter(id__lt=int(older_than))

    def prepare_data(self):
        u_messages = super().prepare_data()
        chat = self.chat.to_dict()
        older_than = self.request.POST.get('older_than')
        if not older_than:
            u_messages = list(reversed(u_messages))
        return {
            'chat': chat,
            'messages': u_messages,
        }

    def dispatch(self, request, *args, **kwargs):
        try:
            self.chat = Chat.objects.get(pk=int(request.POST.get('ci')))
        except:
            return JsonResponse({
                'ok': False,
                'messages': [
                    'CHATS_DOES_NOT_EXIST',
                ],
            })

        return super().dispatch(request, *args, **kwargs)


class ShowMessage(LoginRequiredMixin, PaginationMixIn, View):
    model = Message
    chat = None
    last_message = None

    def validate_data(self):
        try:
            self.chat = Chat.objects.get(pk=int(self.request.POST.get('ci')))
            self.last_message = Message.objects.get(pk=int(self.request.POST.get('lmi')))
        except Exception as e:
            return JsonResponse({
                'ok': False,
                'messages': [
                    'OBJECT_DOES_NOT_EXIST' if isinstance(e, Model.DoesNotExist) else 'BAD_PARAMETERS'
                ],
            })

    def prepare_qs(self):
        if self.chat and self.last_message:
            self.qs = self.qs.filter(chat=self.chat, id__gt=self.last_message.id)


class GetMessage(LoginRequiredMixin, PaginationMixIn, View):
    model = Message

    def prepare_qs(self):
        message_id = self.request.POST.get('message_id')

        if message_id:
            self.qs = self.qs.filter(pk=int(message_id))


class CreateMessage(LoginRequiredMixin, CreateView):

    def post(self, request):
        message_form = MessageCreationForm(self.request.POST, self.request.FILES)
        if not message_form.is_valid():
            return JsonResponse({
                'ok': False,
                'messages': [
                    'BAD_PARAMETERS'
                ]
            })
        message_form.save()
        return JsonResponse({'ok': True})


class UpdateMessage(LoginRequiredMixin, View):

    def post(self, request):
        message_id = request.POST.get('message_id')
        try:
            message = Message.objects.get(pk=int(message_id))

            text = request.POST.get('text', '').strip()
            if text and isinstance(text, str) and len(text) > 0:
                message.text = text
                message.save()
            else:
                raise Exception()
        except:
            return JsonResponse({
                'ok': False,
                'messages': [
                    'BAD_PARAMETERS'
                ]
            })
        return JsonResponse({'ok': True})


class DeleteMessage(LoginRequiredMixin, View):

    def post(self, request, pk):
        try:
            message = get_object_or_404(Message, pk=pk)
            message.delete()
            return JsonResponse({'ok': True})
        except:
            pass
        return JsonResponse({'ok': False})
