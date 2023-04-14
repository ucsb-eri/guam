from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional
import secrets
import subprocess
import os
import re


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")

#generate a 10 character password, this should be moved into the user creation loop so passwords are unique per user instead of per session
pw_length = 10
password = secrets.token_urlsafe(pw_length) + "!"

#dict of servers / paths, we do this to make it easier to add and remove servers / paths
afsserverlist = []
afsserverdict = {
    "autofs-home.eri.ucsb.edu": ["/raid/users-eri/", "/raid/staff-eri/", "/raid/services-eri/", "/raid/users-nrs/",
                                 "/raid/users-msi/", "/raid/staff-msi/", "/raid/services-msi/"],
    "ratl.eri.ucsb.edu": ["/raid/users-eeg/"], "range.eri.ucsb.edu": ["/raid/users-chg/", "/raid/services-chg/"],
    "twe.eri.ucsb.edu": ["/raid/r.r/ccber/ccber-data/CCBER-Staff/"],
    "hoodoo.geog.ucsb.edu": ["/raid/users-geog/", "/raid/staff-geog/", "/raid/grad-geog/", "/raid/services-geog/"],
    "strata.geog.ucsb.edu": ["/raidg/classes-geog/"], "ohv-08.geog.ucsb.edu": ["/raida/users-grit/"]}
for i in afsserverdict:
    for x in afsserverdict[i]:
        afsserverlist.append(i + ":" + x)

@app.post("/result")
def form_post(request: Request, username: str = Form(...), fname: str = Form(...), lname: str = Form(...),
              email: str = Form(...), afsusergroup: Optional[str] = Form(None), destinationbox: Optional[list] = Form(None)):
    username = username
    fname = fname
    lname = lname
    email = email
    destinationbox = destinationbox
    afsusergroup = afsusergroup
    afsusergroups = ['test', 'banana']
    print(username, fname)
    result = fname, username, lname, email, afsusergroup, destinationbox
    return templates.TemplateResponse('index.html', context={'request': request, 'result': result, 'afsusergroups': afsusergroups})


@app.get("/form")
def form_post(request: Request):
    result = "Type a number"
    return templates.TemplateResponse('form.html', context={'request': request, 'result': result})

@app.post("/form")
def form_post(request: Request):
    result = "Type a number"
    return templates.TemplateResponse('form.html', context={'request': request, 'result': result})

@app.get("/")
def form_post(request: Request):
    result = ""
    afsusergroups = ['test', 'banana']
    return templates.TemplateResponse('index.html', context={'request': request, 'result': result, 'afsusergroups': afsusergroups})
