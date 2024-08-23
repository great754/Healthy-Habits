from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from .models import User, Habit, Log, Journal
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import datetime
import matplotlib.pyplot as plt
import base64
from io import BytesIO


# Create your views here.
@login_required
def index(request):
    return render(request, "habits/index.html", {
        "habits": Habit.objects.filter(current_user = request.user)
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "habits/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "habits/login.html")
    
    
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "habits/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "habits/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "habits/register.html")
@login_required   
def create(request):
    if request.method == 'POST':
        title = request.POST["title"]
        description = request.POST["description"]
        date = request.POST["date"]
        how_often = request.POST["often"]
        time_often = request.POST["time"]
        if Habit.objects.filter(current_user = request.user, name=title).exists():
            return HttpResponseRedirect(reverse("index"))
        else:
            Habit(current_user = request.user, name=title, description = description, date_started=date, how_often = how_often, time_often = time_often).save()
        return HttpResponseRedirect(reverse("index"))  
    else:
        choices = []
        choices2=[]
        how_often = Habit.choices
        time_often = Habit.times
        for choice in how_often:
            choices.append(choice[1])
        for choice in time_often:
            choices2.append(choice[1])
        return render(request, "habits/create.html", {
            "how_often": choices,
            "time_often": choices2
        })
    
@login_required
def habit(request, id):
    ## ## add how_often and time_often variables to returned
    habit = Habit.objects.get(pk=id)
    if habit.current_user != request.user:
        return HttpResponse("You do not have access to view this")
    today = datetime.datetime.now().date()
    started = today - datetime.timedelta(days=13)
    interval = []
    days_between = (today - started).days
    for i in range(days_between + 1):
        interval.append(today - datetime.timedelta(days=i))
    all_logs = []
    for day in interval:
        if Log.objects.filter(habit=habit, user=request.user, when=day).exists():
            for log in Log.objects.filter(habit=habit, user=request.user, when=day):
                all_logs.append((log.when.strftime("%Y-%m-%d"), calculate(log.id)))
        else:
            all_logs.append((day.strftime("%Y-%m-%d"), 0))


    x = []
    y = []
    for log in all_logs:
        x.append(log[0])
        y.append(log[1])
    x.reverse()
    y.reverse()
    # Plot the graph
    plt.figure(figsize=(5, 4))
    plt.plot(x, y, marker='o')
    plt.title(f'{habit.name} Progress')
    plt.xlabel('Date')
    plt.ylabel('Time Spent (minutes)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    graph = get_graph()
    choices = []
    choices2=[]
    how_often = Habit.choices
    time_often = Habit.times
    for choice in how_often:
        choices.append(choice[1])
    for choice in time_often:
        choices2.append(choice[1])

    if streak(request, id):
        return render(request, "habits/habit.html", {
            "logs": Log.objects.filter(habit = Habit.objects.get(pk=id)),
            "habit": Habit.objects.get(pk=id),
            "hit": "true",
            "graph": graph,
            "count": count(request, id),
            "how_often": choices,
            "time_often": choices2
        })
    else:
        return render(request, "habits/habit.html", {
            "logs": Log.objects.filter(habit = Habit.objects.get(pk=id)),
            "habit": Habit.objects.get(pk=id),
            "graph": graph,
            "count": count(request, id),
            "how_often": choices,
            "time_often": choices2
        })

@login_required
def log(request):
    if request.method == 'POST':
        title = request.POST["title"]
        habit = Habit.objects.get(name=title, current_user = request.user)
        date = request.POST["when"]
        start = request.POST["started"]
        end = request.POST["ended"]
        Log(user = request.user, habit = habit, when = date, started = start, ended = end).save()
        return HttpResponseRedirect(reverse("habit", kwargs={'id':habit.id}))
    else: 
        return render(request, "habits/log.html", {
            "habits": Habit.objects.filter(current_user = request.user)
        })
    

def calculate(id):
    log = Log.objects.get(pk=id)
    started = str(log.started)
    ended = str(log.ended)
    hour1, minute1, second1 = started.split(":")
    hour2, minute2, second2 = ended.split(":")
    minutes1 = (int(hour1)*60)+int(minute1)
    minutes2 = (int(hour2)*60)+int(minute2)
    return minutes2 - minutes1

## journal with log_id
@login_required
def journal(request, id):
    log = Log.objects.get(pk=id)
    if request.method == 'POST':
        log = Log.objects.get(pk=id)
        title = request.POST["title"]
        entry = request.POST["entry"]
        user = request.user
        Journal(user=user, title=title, log=log, entry=entry).save()
        return HttpResponseRedirect(reverse("habit", kwargs={'id': log.habit.id}))
    else:
        if Journal.objects.filter(log=log).exists():
            if Log.objects.get(pk=id).user != request.user:
                return HttpResponse("You do not have access to view this page")
            else:
                return render(request, "habits/journal.html", {
                    "log": Log.objects.get(pk=id),
                    "journal": Journal.objects.get(log=log)
                })
        else:
            if Log.objects.get(pk=id).user != request.user:
                return HttpResponse("You do not have access to view this page")
            return render(request, "habits/journal.html", {
                "log": Log.objects.get(pk=id)
            })
        
def streak(request, id):
    habit = Habit.objects.get(pk=id)
    if habit.how_often.lower() == 'weekly':
        ## Get everything from the start of the week till now
        today = datetime.datetime.now().date()
        start = today - datetime.timedelta(days=today.weekday() + 1)
        daysbetween = today.day - start.day
        interval = []
        for i in range(daysbetween+1):
            interval.append(today - datetime.timedelta(days=i))
        week_logs = []
        for day in interval:
            if (Log.objects.filter(when=day, user=request.user, habit=habit).exists()):
                for log in Log.objects.filter(when=day, user=request.user, habit=habit):
                    week_logs.append(log)
        if len(week_logs) >= int(habit.time_often):
            #return HttpResponse("Hit Goal!")
            return True
        else:
            #return HttpResponse("Nope")
            return False
        
    if habit.how_often.lower() == 'daily':
        ## Get all the logs today
        today = datetime.datetime.now().date()
        day_logs = []
        if (Log.objects.filter(when=today, user=request.user, habit=habit).exists()):
            for log in Log.objects.filter(when=today, user=request.user, habit=habit):
                day_logs.append(log)
        if len(day_logs) >= int(habit.time_often):
            #return HttpResponse("Hit Daily Goal!")
            return True
        else:
            # return HttpResponse("Did not Hit")
            return False
        
    if habit.how_often.lower() == 'monthly':
        start = datetime.date(today.year, today.month, 1)
        daysbetween = today.day - start.day
        interval = []
        for i in range(daysbetween+1):
            interval.append(today - datetime.timedelta(days=i))
        month_logs = []
        for day in interval:
            if (Log.objects.filter(when=day, user=request.user, habit=habit).exists()):
                for log in Log.objects.filter(when=day, user=request.user, habit=habit):
                    month_logs.append(log)
        if len(month_logs) >= int(habit.time_often):
            return True
        else:
            return False
    
    if habit.how_often.lower() == 'yearly':
        start = datetime.date(today.year, 1, 1)
        daysbetween = (today - start).days
        interval = []
        for i in range(daysbetween+1):
            interval.append(today - datetime.timedelta(days=i))
        year_logs=[]
        for day in interval:
            if (Log.objects.filter(when=day, user=request.user, habit=habit).exists()):
                for log in Log.objects.filter(when=day, user=request.user, habit=habit):
                    year_logs.append(log)
        if len(year_logs) >= int(habit.time_often):
            return True
        else:
            return False

def get_graph():
    buffer = BytesIO()
    plt.savefig(buffer, format="png", transparent=True)
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph



def count(request, id):
    today = datetime.datetime.now().date()
    habit = Habit.objects.get(pk=id)
    if habit.how_often.lower() == 'weekly':
        start = today - datetime.timedelta(days=today.weekday() + 1)
        daysbetween = today.day - start.day
        interval = []
        for i in range(daysbetween+1):
            interval.append(today - datetime.timedelta(days=i))
        week_logs = []
        for day in interval:
            if (Log.objects.filter(when=day, user=request.user, habit=habit).exists()):
                for log in Log.objects.filter(when=day, user=request.user, habit=habit):
                    week_logs.append(log)
        return len(week_logs)
    
    elif habit.how_often.lower() == 'daily':
        day_logs = []
        if (Log.objects.filter(when=today, user=request.user, habit=habit).exists()):
            for log in Log.objects.filter(when=today, user=request.user, habit=habit):
                day_logs.append(log)
        return len(day_logs)
    
    elif habit.how_often.lower() == 'monthly':
        start = datetime.date(today.year, today.month, 1)
        daysbetween = today.day - start.day
        interval = []
        for i in range(daysbetween+1):
            interval.append(today - datetime.timedelta(days=i))
        month_logs = []
        for day in interval:
            if (Log.objects.filter(when=day, user=request.user, habit=habit).exists()):
                for log in Log.objects.filter(when=day, user=request.user, habit=habit):
                    month_logs.append(log)
        return len(month_logs)
    
    else:
        start = datetime.date(today.year, 1, 1)
        daysbetween = (today - start).days
        interval = []
        for i in range(daysbetween+1):
            interval.append(today - datetime.timedelta(days=i))
        year_logs=[]
        for day in interval:
            if (Log.objects.filter(when=day, user=request.user, habit=habit).exists()):
                for log in Log.objects.filter(when=day, user=request.user, habit=habit):
                    year_logs.append(log)
        return len(year_logs)

@login_required
@csrf_exempt
def edit(request, id):
    try:
        habit = Habit.objects.get(pk=id)
        if habit.current_user != request.user:
            return JsonResponse({"error": "You do not have access to edit this Habit"})
        else:
            data = json.loads(request.body)
            habit.name = data.get("title", "")
            habit.description = data.get("description", "")
            habit.how_often = data.get("how_often", "")
            habit.time_often = data.get("time_often", "")
            habit.save()
            return JsonResponse({"message": "Edited successfully!"})
    except Habit.DoesNotExist:
        return JsonResponse({"error": "Post Not Found"})

def delete(request, id):
    if request.method == 'POST':
        habit = Habit.objects.get(pk=id)
        habit.delete()
        return HttpResponseRedirect(reverse(index))
    else:
        return HttpResponse("<h1 style='text-align:center;'> Error 404 </h1> <h3 style='text-align:center;'> Page Does Not Exist </h3>")