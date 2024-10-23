from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
from pydantic import BaseModel
import secrets
import subprocess
import os
import re
import utils

##########################################Globals
config = utils.read_config()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")

group = re.compile(r"(?<=^nisMapName: ).*$", re.MULTILINE)  # regex to filter out autofs map names from ldbsearch, ie auto.chc or auto.grit
groupname = re.compile(r"(?<=OU=).*(?=,OU)", re.MULTILINE)  # regex to filter out autofs group OU names from ldbsearch
uidstrip = re.compile(r"^uidNumber: ", re.MULTILINE)
gidstrip = re.compile(r"^gidNumber: ", re.MULTILINE)
secgroupregex = re.compile(r"(?<=^dn: CN=)[^,]+|(?<=^gidNumber: ).*$", re.MULTILINE)  # extract just the CN from the DN
#generate a 10 character password, this should be moved into the user creation loop so passwords are unique per user instead of per session
pw_length = 10
#password = secrets.token_urlsafe(pw_length) + "!"
autofssettings = "-nolock,rw,soft,vers=4"

#dict of servers / paths, we do this to make it easier to add and remove servers / paths
secgroupdict = {}
afsserverlist = []
afsserverdict = config.get("afsserver", {})
for i in afsserverdict:
    for x in afsserverdict[i]:
        afsserverlist.append(i + ":" + x)

departmentlist = config.get("departmentlist", [])

################################################Regular Calls

#generate the list of security groups
#def Convert(secgroups):
#    print(secgroups)
#    res_dct = {secgroups[i]: secgroups[i + 1] for i in range(0, len(secgroups), 2)}
#    return res_dct
def Convert(secgroups):
    res_dct = {secgroups[i]: secgroups[i + 1] for i in range(0, len(secgroups) - 1, 2)}
    return res_dct


#get the list of autofs groups
def dropdown():  # define the data to be sent to the webui containing the list of existing autofs groups in AD
    stream = os.popen(
        'sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b ou=AutoFS,DC=grit,DC=ucsb,DC=edu')
    output = stream.read()
    rawafsgroups = group.findall(output)
    dedupafsgroups = list(dict.fromkeys(rawafsgroups))
    dedupafsgroups.remove("auto.master")
    afsgroups = dedupafsgroups
    afsusergroups = dedupafsgroups
    secgroupcommand = os.popen(
        'sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b "OU=GRIT Users,DC=grit,DC=ucsb,DC=edu" \'(sAMAccountType=268435456)\'')
    rawsecgroups = secgroupcommand.read()
    secgroups = secgroupregex.findall(rawsecgroups)
    secgroupdict = Convert(secgroups)
    secgrouplist = list(secgroupdict.keys())
    secgrouplist.sort(key=str.casefold)
    return afsusergroups, secgrouplist, afsgroups, secgroupdict # return the dropdown data

######add user
def addUser(form_data, usersecgroup, afsusergroup):
    afsusergroups, secgrouplist, afsgroups, secgroupdict = dropdown()
    password = secrets.token_urlsafe(pw_length) + "!"
    uidsearchcommand = os.popen('sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b DC=grit,DC=ucsb,DC=edu \'(uidNumber=5****)\' | grep uidNumber')
    uidsearchresult = uidsearchcommand.read()
    uidresultstrip = re.sub(uidstrip, '', uidsearchresult)
    uidresultsplit = (uidresultstrip.split('\n'))
    maxuid = max(uidresultsplit)
    newuid = int(maxuid) + 1
    secondaryGID = usersecgroup
    primaryGID = form_data["userprimarygroup"]
    result = form_data
    gid = secgroupdict.get(primaryGID)
    print(newuid)
    open("/tmp/useradd.ldif", 'w').close()
    open("/tmp/userafsadd.ldif", 'w').close()
    
    # Adding user with department in LDIF
    adduser_ldif = f"""
dn: CN={result['username']},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: user
cn: {result['username']}
sn: {result['lname']}
givenName: {result['fname']}
displayName: {result['fname']} {result['lname']}
name: {result['username']}
homeDirectory: /home/{result['username']}
sAMAccountName: {result['username']}
userPrincipalName: {result['username']}@grit.ucsb.edu
uidNumber: {newuid}
gidNumber: {gid}
unixHomeDirectory: /home/{result['username']}
loginShell: /bin/bash
mail: {result['email']}
department: {result['department']}
description: {result['description']}
userAccountControl: 512
"""
    with open("/tmp/useradd.ldif", "a") as userfile:
        userfile.write(adduser_ldif)
    
    adduser_command = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/useradd.ldif"
    sp = subprocess.Popen([adduser_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    command_result = sp.stdout.read().decode()

    addtoprimarygroup = "sudo samba-tool group addmembers '" + form_data["userprimarygroup"] + "' " + result['username']
    primarygroupaddcommand = subprocess.Popen([addtoprimarygroup], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    primarygroupadd_result = primarygroupaddcommand.stdout.read().decode()
    print(primarygroupadd_result)
    print(secondaryGID)
    if secondaryGID:
        for j in secondaryGID:
            addtogroup = "sudo samba-tool group addmembers '" + j + "' " + result['username']
            groupaddcommand = subprocess.Popen([addtogroup], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            groupadd_result = groupaddcommand.stdout.read().decode()
            print(groupadd_result)
    else:
        groupadd_result = "no secondary groups added"
    display = 'visible'
    usergroups = afsusergroup
    for i in usergroups:
        print("adding lines to ldif")
        x = i.replace('auto.', '')
        adduserafs = f"""dn: CN=/home/{form_data["username"]},CN={i},OU={x.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: /home/{form_data["username"]}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: /home/{form_data["username"]}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: {i}
nisMapEntry: {autofssettings} {form_data["userafsserver"]}{form_data["username"]}
distinguishedName: CN=/home/{form_data["username"]},CN={i},OU={x.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
"""
        print(adduserafs)
        with open("/tmp/useraddafs.ldif", "a") as userfile:
            userfile.write(adduserafs)
            print("added to ldif")
        userfile.close()
    adduserafsall = f"""dn: CN=/home/{form_data["username"]},CN=auto.ALL,OU=ALL,OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: /home/{form_data["username"]}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: /home/{form_data["username"]}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: auto.ALL
nisMapEntry: {autofssettings} {form_data["userafsserver"]}{form_data["username"]}
distinguishedName: CN=/home/{result['username']},CN=auto.ALL,OU=ALL,OU=AutoFS,DC=grit,DC=ucsb,DC=edu

dn: CN=/var/www/nextcloud-data/{result['username']},CN=auto.Nextcloud,OU=Nextcloud,OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: /var/www/nextcloud-data/{result['username']}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: /var/www/nextcloud-data/{result['username']}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: auto.Nextcloud
nisMapEntry: {autofssettings} {form_data["userafsserver"]}{form_data["username"]}
distinguishedName: CN=/var/www/nextcloud-data/{result['username']},CN=auto.Nextcloud,OU=Nextcloud,OU=AutoFS,DC=grit,DC=ucsb,DC=edu"""
    with open("/tmp/userafsadd.ldif", "a") as afsfile:
        afsfile.write(adduserafsall)
    afsfile.close()
    if "ERROR(ldb): Failed to add user" in command_result:
        ldif_result = "ERROR"
        return result, display, command_result, ldif_result, gid
    else:
        ldif_result = "SUCCESS"
        adduserafsldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/userafsadd.ldif"
        #writeldif = subprocess.Popen([adduser_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        #ldif_result = writeldif.stdout.read().decode()
        writeafsldif = subprocess.Popen([adduserafsldif], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        afsldif_result = writeafsldif.stdout.read().decode()
        print(afsldif_result)
    print(form_data["userafsserver"])
    zfsserverpath = re.sub('.*:\/', '', form_data["userafsserver"])
    afsserverpath = re.sub('^.*:', '', form_data["userafsserver"])
    autofsserver = re.sub(':.*$', '', form_data["userafsserver"])
    server = "gritadm@" + autofsserver
    print(afsserverpath + form_data["username"])

#    sshProcess = subprocess.Popen(['ssh', '-T', server, "sudo zfs create " + zfsserverpath + form_data["username"] + " && sudo zfs set quota=300g refquota=50g " + zfsserverpath + form_data["username"] + " && sudo chown " + str(newuid) + ":" + str(gid) + " " + afsserverpath + form_data["username"] + " && echo "" | sudo tee -a /etc/exports && echo \"" + afsserverpath + form_data["username"] + " \\\\\" | sudo tee -a /etc/exports && echo \"128.111.100.0/23(rw,no_root_squash) \\\\\" | sudo tee -a /etc/exports && echo \"128.111.236.0/24(rw,no_root_squash) \\\\\" | sudo tee -a /etc/exports && echo \"128.111.104.0/24(rw,no_root_squash)\" | sudo tee -a /etc/exports && sudo systemctl restart nfs-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    
    nfscommand = f"""
sudo zfs create {zfsserverpath}{form_data["username"]} && \
sudo zfs set quota=300g refquota=50g {zfsserverpath}{form_data["username"]} && \
sudo chown {newuid}:{gid} {afsserverpath}{form_data["username"]} && \
sudo bash -c 'cat <<EOF >> /etc/exports
{afsserverpath}{form_data["username"]} \\
128.111.100.0/23(rw,no_root_squash) \\
128.111.236.0/24(rw,no_root_squash) \\
128.111.104.0/24(rw,no_root_squash)
EOF' && \
sudo systemctl restart nfs-server
""" 
    sshProcess = subprocess.Popen(['ssh', '-T', server, nfscommand], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    sshProcess_result = sshProcess.stdout.read().decode()
    result = "form input: " + str(result) + " user add command result: " + command_result + " home folder autofs command result: " + ldif_result + " group add command output: " + groupadd_result + " home folder creation result: " + sshProcess_result
    return result

##########

def addAutofsEntry(form_data, afsgroup):
    result = form_data
    open("/tmp/afsgroupadd.ldif", 'w').close()
    addafsldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/afsgroupadd.ldif"
    for afs in afsgroup:
        y = afs.strip('auto.')
        addafsgroup = f"""dn: CN={result['autofsmountpoint']},CN={afs},OU={y.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: {result['autofsmountpoint']}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: {result['autofsmountpoint']}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: {afs}
nisMapEntry: -nolock,rw,soft,vers=4 {result['autofspath']}
distinguishedName: CN={result['autofsmountpoint']},CN={afs},OU={y.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu"""
        with open("/tmp/afsgroupadd.ldif", "a") as file:
            file.write(addafsgroup)
    file.close()
    writeafsldif = subprocess.Popen([addafsldif], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ldif_afs_result = writeafsldif.stdout.read().decode()
    result = "form input: " + str(result) + " ldif command output: " + str(ldif_afs_result)
    return result

###########

def AddSecGroup(form_data):
    open("/tmp/secgroupadd.ldif", 'w').close()
    addsecgroupldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/secgroupadd.ldif"
    result = form_data
    gidsearchcommand = os.popen('sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b DC=grit,DC=ucsb,DC=edu \'(gidNumber=48***)\' | grep gidNumber')
    gidsearchresult = gidsearchcommand.read()
    gidresultstrip = re.sub(gidstrip, '', gidsearchresult)
    gidresultsplit = (gidresultstrip.split('\n'))
    maxgid = max(gidresultsplit)
    newgid = int(maxgid)+1
    addsecgroup = f"""dn: CN={result['groupname']},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: group
description: {result['groupdesc']}
cn: {result['groupname']}
instanceType: 4
name: {result['groupname']}
sAMAccountName: {result['groupname']}
objectCategory: CN=Group,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
gidNumber: {newgid}
distinguishedName: CN={result['groupname']},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu"""
    with open("/tmp/secgroupadd.ldif", "a") as file:
        file.write(addsecgroup)
    file.close()
    writesecgroupldif = subprocess.Popen([addsecgroupldif], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ldif_secgroup_result = writesecgroupldif.stdout.read().decode()
    result = "form input: " + str(result) + " ldif command output: " + ldif_secgroup_result + " newgid: " + str(newgid)
    return result

############

def AddAutofsGroup(form_data, grouplist):
    result = form_data
    grouplist = result['w3review']
    ' '.join(str(e) for e in grouplist)
    grouplist = str(grouplist).split(r'\r\n')
    grouplist = [s.replace("[", "") for s in grouplist]
    grouplist = [s.replace("]", "") for s in grouplist]
    grouplist = [s.replace("'", "") for s in grouplist]
    open("/tmp/afsgroupnew.ldif", 'w').close()
    addafsnewldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/afsgroupnew.ldif"
    for each in grouplist:
        afsnewgroup = f"""dn: OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: organizationalUnit
ou: {each}
instanceType: 4
name: {each}
objectCategory: CN=Organizational-Unit,CN=Schema,CN=Configuration,DC=grit,DC=u
 csb,DC=edu
distinguishedName: OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=edu

dn: CN=auto.master,OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisMap
cn: auto.master
instanceType: 4
showInAdvancedViewOnly: TRUE
name: auto.master
objectCategory: CN=NisMap,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: auto.master
distinguishedName: CN=auto.master,OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=edu

dn: CN=/-,CN=auto.master,OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: /-
instanceType: 4
showInAdvancedViewOnly: TRUE
name: /-
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: auto.master
nisMapEntry: auto.{each}
distinguishedName: CN=/-,CN=auto.master,OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=e
 du

dn: CN=auto.{each},OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisMap
cn: auto.{each}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: auto.{each}
objectCategory: CN=NisMap,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: auto.{each}
distinguishedName: CN=auto.{each},OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=edu"""
        with open("/tmp/afsgroupnew.ldif", "a") as file:
            file.write(afsnewgroup)
    file.close()
    writeafsnewldif = subprocess.Popen([addafsnewldif], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ldif_afs_result = writeafsnewldif.stdout.read().decode()
    result = "form input: "+ str(result) + " ldif command output: " + str(ldif_afs_result)
    return result



##################################################Main Loop

@app.post("/")
async def submit_form(request: Request, usersecgroup: list = Form(...), afsusergroup: list = Form(...), afsgroup: list = Form(...), grouplist: list = Form(...)):
    form_data = await request.form()
    requestType = form_data["submit_button"]
    if requestType == 'AddUser': 
        result = addUser(form_data, usersecgroup, afsusergroup)
    elif requestType == 'AddAutofsEntry':
        result = addAutofsEntry(form_data, afsgroup)
    elif requestType == 'AddSecGroup':
        result = AddSecGroup(form_data)
    elif requestType == 'AddAutofsGroup':
        result = AddAutofsGroup(form_data, grouplist)
    request={}
    afsusergroups, secgrouplist, afsgroups, secgroupdict = dropdown() 
    print(result)
    return templates.TemplateResponse('index.html', context={'request': request, 'result': result, 'afsusergroups': afsusergroups, 'afsserverlist': afsserverlist, 'afsgroups': afsgroups, 'secgrouplist': secgrouplist, 'departmentlist': departmentlist})

@app.get("/")
def form_post(request: Request):
    result = ""
    afsusergroups, secgrouplist, afsgroups, secgroupdict = dropdown()
    return templates.TemplateResponse('index.html', context={'request': request, 'result': result, 'afsusergroups': afsusergroups, 'afsserverlist': afsserverlist, 'afsgroups': afsgroups, 'secgrouplist': secgrouplist, 'departmentlist': departmentlist})

####################################################Testing

# stuff below is testing for the autofs existing entries copy
class Option(BaseModel):
    text: str
    value: str

source_data = {
    "source1": [
        {"text": "Option 1", "value": "1"},
        {"text": "Option 2", "value": "2"},
    ],
    "source2": [
        {"text": "Option 3", "value": "3"},
        {"text": "Option 4", "value": "4"},
    ],
}

destination_data = {
    "destination1": [
        {"text": "Option 5", "value": "5"},
        {"text": "Option 6", "value": "6"},
    ],
    "destination2": [
        {"text": "Option 7", "value": "7"},
        {"text": "Option 8", "value": "8"},
    ],
}

@app.get("/source/{source_id}", response_model=List[Option])
async def get_source_options(source_id: str):
    return source_data.get(source_id, [])

@app.get("/destination/{destination_id}", response_model=List[Option])
async def get_destination_options(destination_id: str):
    return destination_data.get(destination_id, [])
