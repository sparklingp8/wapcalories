from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from .models import Event
# Create your views here.
import time
from datetime import datetime, timedelta
import json
import random
import hashlib

def robots_txt(request):
    content = "User-agent: *\nDisallow: /"
    return HttpResponse(content, content_type="text/plain")

def check_username(request, username):
    """AJAX endpoint to check if username exists"""

    exists = Event.objects.filter(creator_id=username.lower()).exists()

    return JsonResponse({'exists': exists})

def add_new_user(request):
    if request.method == 'POST':
        try:

            username = request.POST.get('euser_name')
            event_name = request.POST.get('event_name')
            target_time = request.POST.get('target_time')
            user_pin = request.POST.get('user_pin')
            confirm_pin = request.POST.get('confirm_user_pin')
            if len(Event.objects.all()) > 100:
                return HttpResponse("Database Full Wait Till Devloper Fix")
            # Check if user exists
            if Event.objects.filter(creator_id=username).exists():

                return redirect('register')  # Redirect back to registration page

            # Continue with user creation if username is unique
            if user_pin != confirm_pin:

                return redirect('register')

            # Create user and save other data



            formatted_time = datetime.strptime(target_time, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")

            formatted_time = formatted_time[:-2]+str(random.randint(10, 60))

            given_time = datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S")

            # Get the current time
            current_time = datetime.now()

            # Calculate the 120-year future limit
            future_limit = current_time + timedelta(days=120 * 365.25)

            # # Check conditions
            # if given_time < current_time:
            #     print("The given time is in the past.")
            #     message = "ERROR !! The given time is in the past."
            #     raise ValueError
            # elif given_time > future_limit:
            #     print("The given time is more than 120 years in the future.")
            #     message  = "ERROR !! The given time is more than 120 years in the future."
            #     raise ValueError
            # else:
            eve_name = event_name
            eve_time = formatted_time
            new_user = Event.objects.create(creator_id=username, creator_pin=int(user_pin))
            new_user.data["events"]=[{
                'event_name': eve_name,
                'target_time': eve_time
            }]
            new_user.save()

            message = f"Success: First *{eve_name}* Countdown added successfully"

            return redirect("user_countdowns", userID=username, message=message)


        # except ValueError as v:
        #     return redirect('register')#redirect("user_countdowns", userID=username, message=message)
        except Exception as e:
            print(e)
            return HttpResponse("something went wrong while registering user")

    else:

        return render(request, 'timeCounter/addNewUser.html')

def user_add_countdown(request, userID):
    message = "yy"

    if request.method == 'POST':
        try:
            # byte_data= request.body
            # d = json.loads(byte_data.decode('utf-8'))
            iso_time = request.POST.get('target_time')
            user_pin = request.POST.get('user_pin')
            try:
                user_pin = int(user_pin)
            except :

                message = f"ERROR !! PIN should contain only Numbers"
                return redirect("user_countdowns", userID=userID, message=message)


            formatted_time = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")

            formatted_time = formatted_time[:-2]+str(random.randint(10, 60))

            given_time = datetime.strptime(formatted_time, "%Y-%m-%d %H:%M:%S")

            # Get the current time
            current_time = datetime.now()

            # Calculate the 120-year future limit
            future_limit = current_time + timedelta(days=120 * 365.25)

            # Check conditions
            if given_time < current_time:

                message = "ERROR !! The given time is in the past."
            elif given_time > future_limit:

                message  = "ERROR !! The given time is more than 120 years in the future."
            else:

                eve_name = request.POST.get('event_name')
                eve_time = formatted_time
                user_id = userID#"ptk"
                user_data = Event.objects.filter(creator_id = user_id).first()
                if user_data.creator_pin == user_pin:
                    if user_data:
                        eves = set()
                        if len(user_data.data['events']) > 10:
                            return HttpResponse("many Events")
                        for e in user_data.data['events']:
                            eves.add(e['event_name'])

                        if eve_name not in eves:
                            user_data.data["events"].append({
                                'event_name': eve_name,
                                'target_time': eve_time
                            })
                            user_data.save()

                            message = f"Success: *{eve_name}* Countdown added successfully"
                        else:

                            message = f"ERROR !!  *{eve_name}* Countdown already exists"
                    else:
                        return HttpResponse(f"{userID}: doesn't exisits in Database, New user adding page coming soon .....")
                        user_data = addUser(userID)
                else:

                    message = f"ERROR !!  *WRONG PIN* try again"

            # Update the dictionary

        except:

            message = f"ERROR !! adding *{request.POST.get('event_name')}* event went something woeing"
            return redirect("user_countdowns", userID=userID, message=message)
    return redirect("user_countdowns", userID=userID, message=message)




def user_delete_countdown(request,userID,count_name):
    user_id = userID#"ptk"
    message = "ERROR !! something went wrong while deleting "
    user_data = Event.objects.filter(creator_id = user_id).first()
    try:
        if user_data:
            events = [event for event in user_data.data['events'] if count_name not in event['event_name'] ]
            user_data.data['events'] = events
            user_data.save()
            print("After deleting", user_data.data['events'])
            message = f"Success: *{count_name}* countdown deleted"
            return redirect("user_countdowns", userID=userID, message =  message)
        else:
            return redirect("user_countdowns", userID=userID, message=message)
    except:
        return redirect("user_countdowns", userID=userID,message=message)

def user_countdown(request, userID, message=""):
    user_id = userID#"ptk"
    user_data = Event.objects.filter(creator_id = user_id).first()

    if user_data :

        if  user_data.data.get("events") and len(user_data.data["events"])>0 :

            timers = user_data.data["events"]

            # Sort the timers list by 'target_time' after converting the string to a datetime object
            timers_sorted = sorted(timers, key=lambda x: datetime.strptime(x['target_time'], '%Y-%m-%d %H:%M:%S'))
            for detail in timers_sorted:
                t = datetime.strptime(detail['target_time'], '%Y-%m-%d %H:%M:%S')
                detail['event_date'] = t.strftime('%d/%m/%Y')

            hashed_value = hashlib.sha256(str(user_data.creator_pin).encode()).hexdigest()
            # Prepare the context
            context = {
                'timers': timers_sorted,
                'timers_json': json.dumps(timers_sorted),  # Pass JSON-serialized data to the template
                'userID': userID,
                'message': message,
                "hashed_value" :hashed_value,
            }

            return render(request, 'timeCounter/time.html', context)
        else:
            hashed_value = hashlib.sha256(str(user_data.creator_pin).encode()).hexdigest()

            context = {
                'timers': "",
                'timers_json': "",  # Pass JSON-serialized data to the template
                'userID': userID,
                'message': message,
                "hashed_value" :hashed_value,
            }
            return render(request, 'timeCounter/time.html', context)

    else:
        return HttpResponse("Wrong URL")





def tryy(request):
    return HttpResponse("hi")

def getAge(request):
    # event.save()
    timers = [
        {
            'event_name': 'Dreams',
            'target_time': '2027-03-07 11:46:46'
        },
        {
            'event_name': 'Mid',
            'target_time': '2040-02-07 23:56:00'
        },
        {
            'event_name': 'Life',
            'target_time': '2067-02-07 23:56:00'
        },
        {
            'event_name': 'Python Master',
            'target_time': '2025-02-26 23:58:02'
        },
        {
            'event_name': 'USA',
            'target_time': '2026-07-04 00:04:08'
        },
    ]

    # Sort the timers list by 'target_time' after converting the string to a datetime object
    timers_sorted = sorted(timers, key=lambda x: datetime.strptime(x['target_time'], '%Y-%m-%d %H:%M:%S'))
    hashed_value = hashlib.sha256(str(0).encode()).hexdigest()

    # Prepare the context
    context = {
        'timers': timers_sorted,
        'timers_json': json.dumps(timers_sorted),
          'userID': 'age',  # Pass JSON-serialized data to the template
          'message': "",
           "hashed_value" :hashed_value,
    }

    return render(request, 'timeCounter/time.html', context)
