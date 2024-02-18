from django.shortcuts import render, redirect
from django.db.models import Q, Count
from django.http import HttpResponse
from base.models import Room, Topic, Message
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from base.form import RoomForm, UserForm


def loginPage(request):
    context = {}

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User not found!')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Incorrect Username or Password !')

    context['page'] = 'login'
    return render(request, 'base/login-register.html', context)


def registerPage(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid submission!')

    return render(request, 'base/login-register.html', {'form': form})


def logoutUser(request):
    logout(request)
    return redirect('home')


def home(request):
    query = request.GET.get('q') if request.GET.get('q') is not None else ''
    total_rooms = Room.objects.count()
    room_messages = Message.objects.all().order_by('-updated')
    rooms = Room.objects.filter(
        Q(topic__name__icontains=query) |
        Q(name__icontains=query) |
        Q(host__username__icontains=query) |
        Q(description__icontains=query)
    )
    if query != '':
        room_messages = room_messages.filter(
            Q(room__topic__name__icontains=query) |
            Q(user__username__icontains=query) |
            Q(body__icontains=query)
        )
    room_count = rooms.count()
    topics = Topic.objects.all().annotate(num_rooms = Count('room')).order_by('-num_rooms')[:4]
    room_messages = room_messages[:10]
    context = {'rooms': rooms, 'topics': topics, 'total_rooms': total_rooms,
               'room_count': room_count, 'room_messages': room_messages, 'query': query}
    return render(request, 'base/home.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    print(rooms)
    topics = Topic.objects.all()
    room_messages = user.message_set.all().order_by('-updated')
    context = {'user': user, 'rooms': rooms,
               'topics': topics, 'room_messages': room_messages}
    return render(request, 'base/user_profile.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)

    if request.method == 'POST':
        new_messages = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('message')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    room_messages = room.message_set.all()
    participants = room.participants.all()
    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name = topic_name)
        room = Room.objects.create(
            host = request.user,
            topic = topic,
            name = request.POST.get('room_name'),
            description = request.POST.get('room_about'),
        )
        # form = RoomForm(request.POST)
        # if form.is_valid:
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     room.save()
        return redirect('room', pk=room.id)
    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    print(room.description)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name = topic_name)
        room.name = request.POST.get('room_name')
        room.topic = topic
        room.description = request.POST.get('room_about')
        room.save()
        return redirect('room', pk=room.id)

    context = {'form': form, 'topics': topics, 'room': room, 'update': True}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'object': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    room_message = Message.objects.get(id=pk)

    if request.user != room_message.user:
        return HttpResponse('You are not allowed here!')

    if request.method == 'POST':
        room_message.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'object': room_message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)
        else:
            messages.error(request, "Invalid Submission")
    return render(request, 'base/update-user.html', {'form': form})

def topicsPage(request):
    query = request.GET.get('q') if request.GET.get('q') is not None else ''
    total_rooms = Room.objects.count()
    topics = Topic.objects.filter(name = query).annotate(num_rooms = Count('room')).order_by('-num_rooms')
    if query == '':
        topics = Topic.objects.all().annotate(num_rooms = Count('room')).order_by('-num_rooms')
    context = {'topics': topics, 'total_rooms': total_rooms}
    return render(request, 'base/topics.html', context)

def activityPage(request):
    room_messages = Message.objects.all().order_by('-updated')
    return render(request, 'base/activity.html', {'room_messages': room_messages})