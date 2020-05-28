        var ps_container = document.querySelector('.messages-container').parentElement;
        ps_container.style.height = window.screen.availHeight - 330 + 'px';
        var ps = new PerfectScrollbar(ps_container);
        var prev_chat_id = null;

        var csrftoken = $("[name=csrfmiddlewaretoken]").val();
        var current_user_id = Number($(".sidebar-users-list-view").attr('data-cu-id'));
        var forward_message_id = null;
        var user_preview_model = '<a href="" class="list-group-item list-group-item-action media"><img class="image-holder" src="{% static 'img/logo.png' %}" alt=""><div class="media-body"><div class="msg-top"><span class="name-holder">سیدمحمد محمدی</span><span class="time-holder"></span></div><p class="msg-summary"></p></div></a>';
        var message_container = $('.messages-container');
        var message_template_container = '<div class="the-messages media mg-t-20"><img  src="https://via.placeholder.com/500" class="user-image-holder wd-36 rounded-circle mg-l-20" alt=""><div class="media-body tx-12"></div></div>'
        var sent_message = `<div class="the-message-container"><div class="chat-holder not-read chat-1"><p class="mb-0"></p><div class="chat-time-container"><span class="chat-time" style="direction: rtl"></span><div class="check-container"><i class="fas fa-check"></i><i class="fas fa-check"></i></div></div></div></div>`;
        var received_message = '<div class="the-message-container"><div class="chat-holder not-read chat-2"><p class="mb-0"></p><div class="chat-time-container"><span class="chat-time" style="direction: rtl"></span><div class="check-container"><i class="fas fa-check"></i><i class="fas fa-check"></i></div></div></div></div>';
        $('#modaldemo1').on('show.bs.modal', function () {
            $('#modaldemo1 .the-cool-loader').removeClass('d-none').addClass('d-flex');
            $('.modal-users-list-view .list-group-item').remove();
            $.ajax('{% url 'user-show-endpoint' %}', {
                method: 'post',
                data: {
                    csrfmiddlewaretoken: csrftoken,
                }
            }).done(function (e) {
                if (e.data.length)
                    for (var u in e.data) {
                        var user = e.data[u];
                        var user_perview_model_clone = $(user_preview_model);
                        user_perview_model_clone.attr('data-user-id', user.id);
                        user_perview_model_clone.click(function (e) {
                            e.preventDefault();
                            $.ajax('{% url 'chat-start-endpoint' %}', {
                                method: 'post',
                                data: {
                                    csrfmiddlewaretoken: csrftoken,
                                    ru: Number(this.getAttribute('data-user-id')),
                                }
                            }).done(function (e) {
                                if (e.ok) {
                                    $('#modaldemo1').modal('hide');
                                    retrieve_new_data();
                                } else {
                                    alert('کاربری که میخواهید برای او پیام ارسال کنید موجود نمی باشد')
                                }
                            })
                        });
                        if (user.avatar)
                            user_perview_model_clone.find('.image-holder').attr('src', user.avatar);
                        user_perview_model_clone.find('.name-holder').text(user.first_name + ' ' + user.last_name);
                        user_perview_model_clone.find('.msg-summary').text(user.username);
                        $('#modaldemo1 .modal-users-list-view').append(user_perview_model_clone);
                    }
                else {
                    console.log('here');
                    $('#modaldemo1 .modal-users-list-view').append($('<p class="list-group-item text-center">شما نمیتوانید به کس دیگری پیام بدهید</p>'));
                }
                $('.the-cool-loader').removeClass('d-flex').addClass('d-none');
            }).fail(function () {
                $('.the-cool-loader').removeClass('d-flex').addClass('d-none');
            })
        });

        var last_user_id = null;
        var last_message_container = null;
        var modal_data = null;

        function show_messages(messages, prepend) {
            for (var m in messages) {
                var message = messages[m];
                var c = last_user_id == null;
                var chat_container;
                var is_sender = false;
                if (message.from_user.id === current_user_id){
                    chat_container = $(sent_message);
                    is_sender = true;
                }
                else
                    chat_container = $(received_message);
                var tt = message.updated ? message.updated_at:message.created_at;
                chat_container.find('.chat-time').text(`${tt[0]}/${tt[1]}/${tt[2]} ${tt[3]}:${tt[4]}:${tt[5]}`)
                console.log(message.seen)
                if (message.seen) {
                    chat_container.find('.chat-holder').removeClass('not-read');
                }
                chat_container.dblclick(function () {
                    $('#modaldemo2').modal('show');
                    modal_data = this;
                });
                var current_message_container;
                var is_same_as_prev = false;
                if (prepend) {
                    var the_one = $('.the-messages').first();
                    if (the_one && the_one.attr('data-ui') && Number(the_one.attr('data-ui')) == message.from_user.id) {
                        is_same_as_prev = true;
                    }
                }

                if (prepend && is_same_as_prev) {
                    chat_container.prepend('<hr class="invisible mg-y-2">');
                    current_message_container = $('.the-messages').first()
                } else if (last_user_id && last_user_id === message.from_user.id && !prepend) {
                    current_message_container = last_message_container;
                    chat_container.prepend('<hr class="invisible mg-y-2">');
                } else {
                    current_message_container = $(message_template_container);
                    if (!c) {
                        current_message_container.addClass('mg-t-20');
                    }
                }

                if (!prepend) {
                    last_message_container = current_message_container;
                    last_user_id = message.from_user.id;
                }

                current_message_container.attr('data-ui', message.from_user.id);

                var the_p = chat_container.find('.chat-holder p');
                the_p.text(message.text);
                the_p.html(the_p.html().split('\n').join('<br>'));

                if (message.file) {
                    var file_address = message.file;
                    if (file_address.match('(.png|.jpg|.jpeg|.tiff)$')) {
                        chat_container.find('.chat-holder').append('<br><br><img style="max-width: 450px" src="' + message.file + '"/>');
                    } else if (file_address.match('(.mkv|.mp4)$')) {
                        chat_container.find('.chat-holder').append('<br><br><video style="max-width: 450px" controls><source src="' + message.file + '" type="video/mp4"></video>');
                    } else if (file_address.match('(.mp3)$')) {
                        chat_container.find('.chat-holder').append('<br><br><audio controls><source src="' + message.file + '" type="video/mp4"></audio>');
                    }
                    chat_container.find('.chat-holder').append('<br><br><a download class="btn btn-primary btn-sm" href="' + message.file + '"> دانلود فایل </a>');
                }
                if (message.chat.id == prev_chat_id) {
                    if (message.from_user.avatar)
                        current_message_container.find('.user-image-holder').attr('src', message.from_user.avatar);
                    chat_container.attr('data-message-id', message.id);
                    if (prepend)
                        current_message_container.find('.media-body').prepend(chat_container);
                    else
                        current_message_container.find('.media-body').append(chat_container);
                    if (!is_sender) {
                        current_message_container.addClass('is-not-sender');
                    }
                    if (prepend)
                        $('#get-older').parent().after(current_message_container);
                    else if (!prepend)
                        message_container.append(current_message_container);
                    if (!prepend)
                        message_container.attr('last-message-id', message.id);
                }
            }
            ps.update();
        }

        function show_chat(chat_id) {
            last_user_id = null;
            last_message_container = null;
            message_container.attr('data-ci', chat_id);
            message_container.find('.the-messages').remove();

            $.ajax('{% url 'chat-detail-endpoint' %}', {
                method: 'post',
                data: {
                    csrfmiddlewaretoken: csrftoken,
                    ci: chat_id,
                }
            }).done(function (e) {
                if (e.ok) {
                    message_container.find('.the-messages').remove();
                    var user = null;
                    if (e.data.chat.from_user.id === current_user_id)
                        user = e.data.chat.to_user;
                    else
                        user = e.data.chat.from_user;
                    $('#to_chat_name').text(user.first_name + ' ' + user.last_name);
                    if (user.avatar)
                        $('#to_chat_pic').attr('src', user.avatar);
                    message_container.attr('data-tu', user.id);
                    if (e.data.messages.length) {
                        show_messages(e.data.messages);
                    } else {
                        message_container.append('<p class="the-messages">شما اولین پیام را ارسال کنید</p>')
                    }
                } else {
                    message_container.find('.the-messages').remove();
                    alert('این چت موجود نمی باشد')
                }
            });
        }

        $('#message-input').keydown(function (e) {
            if (e.ctrlKey && e.key === 'Enter')
                $('#send-message-button').click();
        });

        $('#send-message-button').click(function () {
            $('body').removeClass('forward');
            var form_data = new FormData();
            form_data.append('csrfmiddlewaretoken', csrftoken);
            var message = $('#message-input').val();
            url = '';
            if (message_container.hasClass('editing')) {
                url = '{% url 'message-update-endpoint' %}';
                form_data.append('message_id', message_container.attr('editing-message-id'));
                form_data.append('text', message);
            }else {
                if ($('.file-to-send')[0].files.length)
                    form_data.append('file', $('.file-to-send')[0].files[0]);
                form_data.append('from_user', String(current_user_id));
                form_data.append('to_user', message_container.attr('data-tu'));
                form_data.append('chat', message_container.attr('data-ci'));
                form_data.append('text', message);
                url = '{% url 'message-create-endpoint' %}';
            }
            $.ajax(url, {
                method: 'post',
                data: form_data,
                enctype: 'multipart/form-data',
                contentType: false,
                processData: false,
            }).done(function (e) {
                if (e.ok) {
                    if (message_container.hasClass('editing')) {
                        let message_id = message_container.attr('editing-message-id');
                        $('[data-message-id="'+ message_id +'"] .chat-holder').text(message.split('\n').join('<br>'));
                    } else {
                        get_latest_messages();
                    }
                    $('#message-input').val('')
                } else {
                    alert('اطلاعات ارسال شده اشتباه است')
                }
            });
        });

        function retrieve_new_data() {
            $.ajax('{% url 'chat-show-endpoint' %}', {
                method: 'post',
                data: {
                    csrfmiddlewaretoken: csrftoken,
                }
            }).done(function (e) {
                $('.sidebar-users-list-view .list-group-item').remove();
                if (e.data.length)
                    for (var u in e.data) {
                        var user = null;
                        var user1 = null;
                        if (e.data[u].from_user.id === current_user_id) {
                            user = e.data[u].to_user;
                            user1 = e.data[u].from_user;
                        } else {
                            user = e.data[u].from_user;
                            user1 = e.data[u].to_user;
                        }
                        var user_perview_model_clone = $(user_preview_model);
                        user_perview_model_clone.attr('data-ci', e.data[u].id);
                        user_perview_model_clone.click(function (a) {
                            return function (e) {
                                var chat_id = this.getAttribute('data-ci');
                                if ($('body').hasClass('forward')){
                                    $.ajax('{% url 'message-create-endpoint' %}', {
                                        method: 'post',
                                        data: {
                                            csrfmiddlewaretoken: csrftoken,
                                            forward_message: forward_message_id,
                                            chat_id: chat_id,
                                        }
                                    }).done(function(e) {
                                    });
                                    $('body').removeClass('forward');
                                }
                                e.preventDefault();
                                prev_chat_id = a;
                                if (message_container.hasClass('editing')) {
                                    message_container.removeClass('editing');
                                    $('#message-input').val('');
                                }
                                show_chat(chat_id)
                            }
                        }(e.data[u].id));
                        if (user.avatar)
                            user_perview_model_clone.find('.image-holder').attr('src', user.avatar);
                        user_perview_model_clone.find('.name-holder').text(user.first_name + ' ' + user.last_name);
                        user_perview_model_clone.find('.msg-summary').text(user.username);
                        $('.sidebar-users-list-view').append(user_perview_model_clone);
                    }
                else {
                    $('.sidebar-users-list-view').append($('<p class="list-group-item text-center">هنوز کسی به شما پیام نداده است</p>'));
                }
            }).fail(function () {
                alert('لطفاً دوباره تلاش کنید')
            })
        }

        retrieve_new_data();

        function get_latest_messages() {
            var chat_id = message_container.attr('data-ci');
            var last_message_id = message_container.attr('last-message-id');
            if (chat_id) {
                $.ajax('{% url 'message-show-endpoint' %}', {
                    method: 'post',
                    data: {
                        csrfmiddlewaretoken: csrftoken,
                        ci: chat_id,
                        lmi: last_message_id
                    }
                }).done(function (e) {
                    if (e.data.length) {
                        show_messages(e.data);
                    }
                });
            }
        }

        setInterval(function () {
            get_latest_messages();
        }, 1000);

        function load_older() {
            var first_the_message = $('.the-messages').first();
            if (first_the_message) {
                first_the_message = first_the_message.find('.the-message-container').first();
                if (first_the_message) {
                    $.ajax('{% url 'chat-detail-endpoint' %}', {
                        method: 'post',
                        data: {
                            csrfmiddlewaretoken: csrftoken,
                            ci: message_container.attr('data-ci'),
                            older_than: first_the_message.attr('data-message-id'),
                        },
                    }).done(function (e) {
                        if (e.data.messages.length) {
                            show_messages(e.data.messages, true);
                        }
                    });
                }
            }
        }

        $(document).ready(function () {
            $(document).keyup(function(e) {
                if (e.key === 'Escape') {
                    if (message_container.hasClass('editing')) {
                        message_container.removeClass('editing');
                        $('#message-input').val('');
                    }
                    if ($('body').hasClass('forward')) {
                        $('body').removeClass('forward');
                    }
                }
            });
            $('#update_all_chats').click(retrieve_new_data);
            $('#update_chat').click(get_latest_messages);
            $('#get-older').click(load_older);
            $('#choose-file-button').click(function (e) {
                $('.file-to-send').click();
            });
            $('#modaldemo2 .context-menu.modal-context-menu a').click(function () {
                var action = this.getAttribute('data-action');
                var message_id = modal_data.getAttribute('data-message-id');
                switch (action) {
                    case 'delete':
                        var url = '{% url 'message-delete-endpoint' pk=0 %}';
                        url = url.substr(0, url.length - 1) + message_id;
                        $.ajax(url, {
                            method: 'post',
                            data: {
                                csrfmiddlewaretoken: csrftoken,
                            }
                        }).done(function (e) {
                            if (e.ok) {
                                if (message_container.hasClass('editing')) {
                                    message_container.removeClass('editing');
                                    $('#message-input').val('');
                                }
                                modal_data.remove();
                                $('#modaldemo2').modal('hide');
                            } else {
                                alert('مشکلی رخ داد');
                            }
                        });
                        break;
                    case 'forward':
                        $('body').addClass('forward');
                        forward_message_id = message_id;
                        $('#modaldemo2').modal('hide');
                        break;
                    case 'edit':
                        $.ajax('{% url 'message-get-endpoint' %}', {
                            method: 'post',
                            data: {
                                csrfmiddlewaretoken: csrftoken,
                                message_id: message_id,
                            }
                        }).done(function (e) {
                            if (e.ok && e.data.length > 0){
                                $('#message-input').val(e.data[0].text);
                                message_container.addClass('editing');
                                message_container.attr('editing-message-id', message_id);
                                $('#modaldemo2').modal('hide');
                            }else {
                                alert('پیام درخواستی شما موجود نمی باشد');
                            }
                        });
                        break;
                }
            });
        });