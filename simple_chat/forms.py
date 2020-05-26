from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm as DUserCreationForm, UserChangeForm
from django.contrib.auth.hashers import make_password
from django.forms import CharField, ImageField, models

from user.models import Message


class UserCreationForm(DUserCreationForm):
    first_name = CharField(error_messages={
        'required': 'نام باید وارد شود'
    })
    last_name = CharField(error_messages={
        'required': 'نام خانوادگی باید وارد شود'
    })
    error_messages = {
        'password_mismatch': 'پسورد و تکرار پسورد با هم یکی نیست',
    }
    avatar = ImageField(required=False)

    def __init__(self, *args, **kwargs):
        self._meta.fields = ('username', 'avatar',)
        self._meta.model = get_user_model()
        super().__init__(*args, **kwargs)
        self.fields['password1'].error_messages['required'] = 'کلمه عبور باید وارد شود'
        self.fields['password2'].error_messages['required'] = 'تکرار کلمه عبور باید وارد شود'


class UserUpdateForm(UserChangeForm):
    avatar = ImageField(required=False)

    def __init__(self, *args, **kwargs):
        self._meta.model = get_user_model()
        self._meta.fields = ['username', 'avatar', 'first_name', 'avatar', 'last_name', 'password']
        super().__init__(*args, **kwargs)
        del self.fields['date_joined']

    def save(self, commit=True):
        saved = super().save(False)
        if len(self.cleaned_data['password']) > 0 and len(self.data['password']) > 0:
            self.instance.password = make_password(self.data['password'])
        self.instance.save()
        return saved


class MessageCreationForm(models.ModelForm):
    class Meta:
        fields = '__all__'
        model = Message
