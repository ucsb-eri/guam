from app.models.user import User
import secrets
import os
import re
from app.utils import groups
import subprocess

pw_length = 10
uidstrip = re.compile(r"^uidNumber: ", re.MULTILINE)
autofssettings = "-nolock,rw,soft,vers=4"

######add user
def addUser(user: User):
    result = {}
#     afsusergroups, secgrouplist, afsgroups, secgroupdict = dropdown()
    password = secrets.token_urlsafe(pw_length) + "!"
    uidsearchcommand = os.popen('sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b DC=grit,DC=ucsb,DC=edu \'(uidNumber=5****)\' | grep uidNumber')
    uidsearchresult = uidsearchcommand.read()
    uidresultstrip = re.sub(uidstrip, '', uidsearchresult)
    uidresultsplit = (uidresultstrip.split('\n'))
    maxuid = max(uidresultsplit)
    newuid = int(maxuid) + 1
    secondaryGID = user.usersecgroup
    primaryGID = user.userprimarygroup
    gid =  groups.secgroups().get(primaryGID)
    open("/tmp/useradd.ldif", 'w').close()
    open("/tmp/userafsadd.ldif", 'w').close()

    # Adding user with department in LDIF
    adduser_ldif = f"""
 dn: CN={user.username},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu
 objectClass: top
 objectClass: person
 objectClass: organizationalPerson
 objectClass: user
 cn: {user.username}
 sn: {user.lname}
 givenName: {user.fname}
 displayName: {user.fname} {user.lname}
 name: {user.username}
 homeDirectory: /home/{user.username}
 sAMAccountName: {user.username}
 userPrincipalName: {user.username}@grit.ucsb.edu
 uidNumber: {newuid}
 gidNumber: {gid}
 unixHomeDirectory: /home/{user.username}
 loginShell: /bin/bash
 mail: {user.email}
 department: {user.department}
 description: {user.description}
 userAccountControl: 512
 """
    with open("/tmp/useradd.ldif", "a") as userfile:
         userfile.write(adduser_ldif)

    adduser_command = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/useradd.ldif"
    sp = subprocess.Popen([adduser_command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    command_result = sp.stdout.read().decode()

    addtoprimarygroup = "sudo samba-tool group addmembers '" + user.userprimarygroup + "' " + user.username
    primarygroupaddcommand = subprocess.Popen([addtoprimarygroup], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    primarygroupadd_result = primarygroupaddcommand.stdout.read().decode()
    print(f"gid {primarygroupadd_result}")
    print(f"sec {secondaryGID}")
    if secondaryGID:
        for j in secondaryGID:
            addtogroup = "sudo samba-tool group addmembers '" + j + "' " + user.username
            groupaddcommand = subprocess.Popen([addtogroup], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            groupadd_result = groupaddcommand.stdout.read().decode()
            print(groupadd_result)
    else:
        groupadd_result = "no secondary groups added"
    display = 'visible'
    usergroups = user.afsusergroup
    for i in usergroups:
        print("adding lines to ldif")
        x = i.replace('auto.', '')
        adduserafs = f"""dn: CN=/home/{user.username},CN={i},OU={x.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
 objectClass: top
 objectClass: nisObject
 cn: /home/{user.username}
 instanceType: 4
 showInAdvancedViewOnly: TRUE
 name: /home/{user.username}
 objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
 nisMapName: {i}
 nisMapEntry: {autofssettings} {user.userafsserver}{user.username}
 distinguishedName: CN=/home/{user.username},CN={i},OU={x.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
 """
        print(adduserafs)
        with open("/tmp/useraddafs.ldif", "a") as userfile:
            userfile.write(adduserafs)
            print("added to ldif")
        userfile.close()
    adduserafsall = f"""dn: CN=/home/{user.username},CN=auto.ALL,OU=ALL,OU=AutoFS,DC=grit,DC=ucsb,DC=edu
 objectClass: top
 objectClass: nisObject
 cn: /home/{user.username}
 instanceType: 4
 showInAdvancedViewOnly: TRUE
 name: /home/{user.username}
 objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
 nisMapName: auto.ALL
 nisMapEntry: {autofssettings} {user.userafsserver}{user.username}
 distinguishedName: CN=/home/{user.username},CN=auto.ALL,OU=ALL,OU=AutoFS,DC=grit,DC=ucsb,DC=edu

 dn: CN=/var/www/nextcloud-data/{user.username},CN=auto.Nextcloud,OU=Nextcloud,OU=AutoFS,DC=grit,DC=ucsb,DC=edu
 objectClass: top
 objectClass: nisObject
 cn: /var/www/nextcloud-data/{user.username}
 instanceType: 4
 showInAdvancedViewOnly: TRUE
 name: /var/www/nextcloud-data/{user.username}
 objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
 nisMapName: auto.Nextcloud
 nisMapEntry: {autofssettings} {user.userafsserver}{user.username}
 distinguishedName: CN=/var/www/nextcloud-data/{user.username},CN=auto.Nextcloud,OU=Nextcloud,OU=AutoFS,DC=grit,DC=ucsb,DC=edu"""
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
    print(user.userafsserver)
    zfsserverpath = re.sub('.*:\/', '', user.userafsserver)
    afsserverpath = re.sub('^.*:', '', user.userafsserver)
    autofsserver = re.sub(':.*$', '', user.userafsserver)
    server = "gritadm@" + autofsserver
    print(afsserverpath + user.username)

 #    sshProcess = subprocess.Popen(['ssh', '-T', server, "sudo zfs create " + zfsserverpath + form_data["username"] + " && sudo zfs set quota=300g refquota=50g " + zfsserverpath + form_data["username"] + " && sudo chown " + str(newuid) + ":" + str(gid) + " " + afsserverpath + form_data["username"] + " && echo "" | sudo tee -a /etc/exports && echo \"" + afsserverpath + form_data["username"] + " \\\\\" | sudo tee -a /etc/exports && echo \"128.111.100.0/23(rw,no_root_squash) \\\\\" | sudo tee -a /etc/exports && echo \"128.111.236.0/24(rw,no_root_squash) \\\\\" | sudo tee -a /etc/exports && echo \"128.111.104.0/24(rw,no_root_squash)\" | sudo tee -a /etc/exports && sudo systemctl restart nfs-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    nfscommand = f"""
 sudo zfs create {zfsserverpath}{user.username} && \
 sudo zfs set quota=300g refquota=50g {zfsserverpath}{user.username} && \
 sudo chown {newuid}:{gid} {afsserverpath}{user.username} && \
 sudo bash -c 'cat <<EOF >> /etc/exports
 {afsserverpath}{user.username} \\
 128.111.100.0/23(rw,no_root_squash) \\
 128.111.236.0/24(rw,no_root_squash) \\
 128.111.104.0/24(rw,no_root_squash)
 EOF' && \
 sudo systemctl restart nfs-server
 """ 
    sshProcess = subprocess.Popen(['ssh', '-T', server, nfscommand], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    sshProcess_result = sshProcess.stdout.read().decode()
    result = "form input: " + str(result) + " user add command result: " + command_result + " home folder autofs command result: " + ldif_result + " group add command output: " + groupadd_result + " home folder creation result: " + sshProcess_result
    print('here')
    return user
