from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import QuerySet, Q
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, CreateView, UpdateView

from simple_chat.forms import UserCreationForm, UserUpdateForm, MessageCreationForm
from user.models import Message, Chat, CUser


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

    def dispatch(self, request, *args, **kwargs):
        if not self.request.user.is_superuser:
            messages.error(request, 'صفحه مورد نظر قابل بازیابی نیست')
            return HttpResponseRedirect(reverse('main-page'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        res = super().form_valid(form)
        self.object.first_name = form.cleaned_data['first_name']
        self.object.last_name = form.cleaned_data['last_name']
        self.object.set_password(form.cleaned_data['password1'])
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

    def dispatch(self, request, *args, **kwargs):
        if request.user:
            if not request.user.is_superuser and kwargs['pk'] != request.user.pk:
                return HttpResponseRedirect(reverse('user-update-page', kwargs={'pk': request.user.pk}))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        res = super().form_valid(form)
        return res

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = get_user_model().objects.all()
        return context

    def get_success_url(self):
        messages.success(self.request, 'کاربر با موفقیت بروزرسانی شد')
        if not self.request.user.is_superuser:
            return reverse('main-page')
        return super().get_success_url()


class UserDelete(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            user = CUser.objects.get(pk=pk)
            if user.is_superuser:
                messages.error(request, 'این کاربر نباید حذف شود')
                return HttpResponseRedirect(reverse('user-page'))
            messages.success(request, 'کاربر با موفقیت حذف شد')
            user.delete()
            return HttpResponseRedirect(reverse('user-page'))
        except:
            messages.error(request, 'کاربر مورد نظر موجود نمیباشد')
            return HttpResponseRedirect(reverse('user-page'))


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
        for data in self.apply_page():
            response_data.append(self.to_dict(data))
        return response_data

    def apply_page(self):
        return self.pg.page(self.page).object_list

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
        self.qs.exclude(from_user=self.request.user).update(seen_at=timezone.now())

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
                    'OBJECT_DOES_NOT_EXIST' if isinstance(e, Message.DoesNotExist) else f'BAD_PARAMETERS {{ {e} }}'
                ],
            })

    def prepare_qs(self):
        if self.chat and self.last_message:
            self.qs = self.qs.filter(chat=self.chat, id__gt=self.last_message.id)

        d = self.qs.exclude(from_user=self.request.user)


class GetSeenMessages(LoginRequiredMixin, PaginationMixIn, View):
    model = Message
    chat = None

    def validate_data(self):
        try:
            self.chat = Chat.objects.get(pk=int(self.request.POST.get('ci')))
        except Exception as e:
            return JsonResponse({
                'ok': False,
                'messages': [
                    'OBJECT_DOES_NOT_EXIST' if isinstance(e, Message.DoesNotExist) else f'BAD_PARAMETERS {{ {e} }}'
                ],
            })

    def prepare_data(self):
        response_data = []
        for data in self.apply_page():
            response_data.append({
                'id': data.id,
                'seen': data.seen_at,
            })
        return response_data

    def prepare_qs(self):
        if self.chat:
            self.qs = self.qs.filter(chat=self.chat).order_by('-id')[:50]


class GetMessage(LoginRequiredMixin, PaginationMixIn, View):
    model = Message

    def prepare_qs(self):
        message_id = self.request.POST.get('message_id')

        if message_id:
            self.qs = self.qs.filter(pk=int(message_id))


class CreateMessage(LoginRequiredMixin, View):

    def post(self, request):
        forward_message = request.POST.get('forward_message')
        chat_id = request.POST.get('chat_id')
        if forward_message:
            if isinstance(forward_message, str) and forward_message.isdigit():
                try:
                    message = Message.objects.get(pk=int(forward_message))
                    chat = Chat.objects.get(pk=int(chat_id))
                    message.pk = None
                    message.chat = chat
                    message.from_user = request.user
                    message.save()
                    return JsonResponse({'ok': True})
                except Exception as e:
                    return JsonResponse({
                        'ok': False,
                        'messages': [
                            'BAD_PARAMETERS'
                        ]
                    })
            else:
                return JsonResponse({
                    'ok': False,
                    'messages': [
                        'BAD_PARAMETERS'
                    ]
                })
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


class MeView(LoginRequiredMixin, View):
    def post(self, request):
        return JsonResponse(request.user.to_dict())
