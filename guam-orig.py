from flask import Flask, render_template, request, make_response, g, session
import configparser
import os
import re
import subprocess
from flask_simpleldap import LDAP
import secrets

app = Flask(__name__)
group = re.compile(r"(?<=^nisMapName: ).*$", re.MULTILINE)  # regex to filter out autofs map names from ldbsearch, ie auto.chc or auto.grit
groupname = re.compile(r"(?<=OU=).*(?=,OU)", re.MULTILINE)  # regex to filter out autofs group OU names from ldbsearch
uidstrip = re.compile(r"^uidNumber: ", re.MULTILINE)
gidstrip = re.compile(r"^gidNumber: ", re.MULTILINE)
secgroupregex = re.compile(r"(?<=^dn: CN=)[^,]+|(?<=^gidNumber: ).*$", re.MULTILINE)  # extract just the CN from the DN
config = configparser.ConfigParser()
config.read('/gritadm/config.txt')
pw_length = 10
password = secrets.token_urlsafe(pw_length) + "!"
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

app.config["LDAP_HOST"] = "dc1.grit.ucsb.edu"  # defaults to localhost
app.config["LDAP_BASE_DN"] = "OU=GRIT Users,dc=grit,dc=ucsb,dc=edu"
app.config["LDAP_USERNAME"] = "CN=guam,OU=GRIT Functional Accounts,DC=grit,DC=ucsb,DC=edu"
app.config["LDAP_PASSWORD"] = config['configuration']['password']
ldap = LDAP(app)


def Convert(secgroups):
    print(secgroups)
    res_dct = {secgroups[i]: secgroups[i + 1] for i in range(0, len(secgroups), 2)}
    return res_dct


secgroupcommand = os.popen(
    'sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b "OU=GRIT Users,DC=grit,DC=ucsb,DC=edu" \'(sAMAccountType=268435456)\'')  # command to extract security groups from AD
rawsecgroups = secgroupcommand.read()  # read output of ldbsearch
secgroups = secgroupregex.findall(rawsecgroups)  # convert security groups and GIDs to list
secgroupdict = Convert(secgroups)  # convert list to dict
secgrouplist = secgroupdict.keys()


@app.route('/', methods=['POST', 'GET'])
@ldap.basic_auth_required
# index page which presents a list of optional prcedures such as adding users or autofs groups
def dropdown():  # define the data to be sent to the webui containing the list of existing autofs groups in AD
    stream = os.popen(
        'sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b ou=AutoFS,DC=grit,DC=ucsb,DC=edu')  # dump output of the autofs OU
    output = stream.read()  # read output of ldbsearch
    rawafsgroups = group.findall(output)  # use the group filter on the ldbsearch output
    dedupafsgroups = list(dict.fromkeys(rawafsgroups))  # remove duplicate group names
    dedupafsgroups.remove("auto.master")  # remove the auto.master nismap name from the list of group names
    secgroupcommand = os.popen(
        'sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b "OU=GRIT Users,DC=grit,DC=ucsb,DC=edu" \'(sAMAccountType=268435456)\'')  # command to extract security groups from AD
    rawsecgroups = secgroupcommand.read()  # read output of ldbsearch
    secgroups = secgroupregex.findall(rawsecgroups)  # convert security groups and GIDs to list
    secgroupdict = Convert(secgroups)  # convert list to dict
    secgrouplist = list(secgroupdict.keys())
    secgrouplist.sort(key=str.casefold)
    return render_template('index.html', afsgroups=dedupafsgroups, afsusergroups=dedupafsgroups,
                           secgrouplist=secgrouplist, afsserverlist=afsserverlist)  # send data to web ui


# output results page, shows any errors or success messages
@app.route('/result', methods=['POST', 'GET'])
def result():
    usergroups = 'none'
    #  command = 'ldbedit -H /var/lib/samba/private/sam.ldb -b OU=AutoFS,DC=grit,DC=ucsb,DC=edu'
    if request.method == 'POST':
        if request.form['submit_button'] == 'submit User':  # submit user operation sent from web ui
            uidsearchcommand = os.popen(
                'sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b DC=grit,DC=ucsb,DC=edu \'(uidNumber=5****)\' | grep uidNumber')
            uidsearchresult = uidsearchcommand.read()  # read output of ldbsearch
            uidresultstrip = re.sub(uidstrip, '', uidsearchresult)
            uidresultsplit = (uidresultstrip.split('\n'))
            maxuid = max(uidresultsplit)
            newuid = int(maxuid) + 1
            result = request.form
            secondaryGID = request.form.getlist('usersecgroup') + request.form.getlist('userprimarygroup')
            primaryGID = request.form['userprimarygroup']
            gid = secgroupdict.get(primaryGID)
            if request.form['username'] == 'username':
                display = 'none'
            else:
                open("/tmp/useradd.ldif", 'w').close()
                open("/tmp/userafsadd.ldif", 'w').close()
                adduser = "sudo samba-tool user create " + result['username'] + " " + password + " --surname=\"" + \
                          result['lname'] + "\" --given-name=" + result['fname'] + " --uid-number " + str(
                    newuid) + " --gid-number " + str(gid) + " --mail-address " + result[
                              'email'] + " --userou=\"ou=GRIT Users\"" + " --use-username-as-cn --unix-home=/home/" + \
                          result['username']  # command to run to add a new user to AD
                addldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/useradd.ldif"
                adduserafsldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/userafsadd.ldif"
                sp = subprocess.Popen([adduser], shell=True, stdout=subprocess.PIPE,
                                      stderr=subprocess.STDOUT)  # run command and capture output
                command_result = sp.stdout.read().decode()
                for j in secondaryGID:
                    addtogroup = "sudo samba-tool group addmembers '" + j + "' " + result['username']
                    groupaddcommand = subprocess.Popen([addtogroup], shell=True, stdout=subprocess.PIPE,
                                                       stderr=subprocess.STDOUT)  # run command and capture output
                    groupadd_result = groupaddcommand.stdout.read().decode()
                    print(groupadd_result)
                display = 'visible'
                usergroups = request.form.getlist('afsusergroup')
                for i in usergroups:
                    print("adding lines to ldif")
                    x = i.replace('auto.', '')
                    adduserafs = f"""dn: CN=/home/{request.form['username']},CN={i},OU={x.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: /home/{request.form['username']}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: /home/{request.form['username']}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: {i}
nisMapEntry: {request.form['autofssettings']} {request.form['userafsserver']}{request.form['username']}
distinguishedName: CN=/home/{request.form['username']},CN={i},OU={x.replace('-home', '')},OU=AutoFS,DC=grit,DC
 =ucsb,DC=edu

"""
                    print(adduserafs)
                    with open("/tmp/useradd.ldif", "a") as userfile:
                        userfile.write(adduserafs)
                        print("added to ldif")
                userfile.close()
                adduserafsall = f"""dn: CN=/home/{request.form['username']},CN=auto.ALL,OU=ALL,OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: /home/{request.form['username']}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: /home/{request.form['username']}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: auto.ALL
nisMapEntry: {request.form['autofssettings']} {request.form['userafsserver']}{request.form['username']} 
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
nisMapEntry: {request.form['autofssettings']} {request.form['userafsserver']}{request.form['username']} 
distinguishedName: CN=/var/www/nextcloud-data/{result['username']},CN=auto.Nextcloud,OU=Nextcloud,OU=AutoFS,DC=grit,DC=ucsb,DC=edu"""
                with open("/tmp/userafsadd.ldif", "a") as afsfile:
                    afsfile.write(adduserafsall)
                afsfile.close()
                if "ERROR(ldb): Failed to add user" in command_result:
                    ldif_result = "ERROR"
                    return render_template("access.html", result=result, display=display, ugroups=usergroups,
                                           command_result=command_result, ldif_result=ldif_result)
                else:
                    writeldif = subprocess.Popen([addldif], shell=True, stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT)
                    ldif_result = writeldif.stdout.read().decode()
                    writeafsldif = subprocess.Popen([adduserafsldif], shell=True, stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT)
                    afsldif_result = writeafsldif.stdout.read().decode()
                    print(afsldif_result)
                print(request.form['userafsserver'])
                zfsserverpath = re.sub('.*:\/', '', request.form['userafsserver'])
                afsserverpath = re.sub('^.*:', '', request.form['userafsserver'])
                autofsserver = re.sub(':.*$', '', request.form['userafsserver'])
                server = "gritadm@" + autofsserver
                print(afsserverpath + request.form['username'])
                sshProcess = subprocess.Popen(['ssh', '-T', server, "zfs create " + zfsserverpath + request.form[
                    'username'] + " && sudo zfs set quota=50g " + zfsserverpath + request.form[
                                                   'username'] + " && sudo chown " + str(newuid) + ":" + str(
                    gid) + " " + afsserverpath + request.form[
                                                   'username'] + " && echo "" | sudo tee -a /etc/exports && echo \"" + afsserverpath +
                                               request.form[
                                                   'username'] + " \\\\\" | sudo tee -a /etc/exports && echo \"128.111.100.0/23(rw,no_root_squash) \\\\\" | sudo tee -a /etc/exports && echo \"128.111.236.0/24(rw,no_root_squash) \\\\\" | sudo tee -a /etc/exports && echo \"128.111.104.0/24(rw,no_root_squash)\" | sudo tee -a /etc/exports && sudo systemctl restart nfs-server"],
                                              stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                sshProcess_result = sshProcess.stdout.read().decode()
            return render_template("access.html", result=result, display=display, ugroups=usergroups,
                                   command_result=command_result, ldif_result=ldif_result,
                                   groupadd_result=groupadd_result, sshProcess_result=sshProcess_result)

        ################################################################################################################################################################

        elif request.form['submit_button'] == 'submit Autofs':  # add new autofs entries to existing groups
            result = request.form
            open("/tmp/afsgroupadd.ldif", 'w').close()
            addafsldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/afsgroupadd.ldif"
            for afs in request.form.getlist('afsgroup'):
                y = afs.strip('auto.')
                addafsgroup = f"""dn: CN={request.form['autofsmountpoint']},CN={afs},OU={y.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: {request.form['autofsmountpoint']}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: {request.form['autofsmountpoint']}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: {afs}
nisMapEntry: -nolock,rw,soft,vers=4 {request.form['autofspath']}
distinguishedName: CN={request.form['autofsmountpoint']},CN={afs},OU={y.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu"""
                with open("/tmp/afsgroupadd.ldif", "a") as file:
                    file.write(addafsgroup)
            file.close()
            writeafsldif = subprocess.Popen([addafsldif], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            ldif_afs_result = writeafsldif.stdout.read().decode()
            return render_template("access.html", result=result, ldif_afs_result=ldif_afs_result)

        ########################################################################################################################
        elif request.form['submit_button'] == 'submit security group':  # add new security group to AD
            open("/tmp/secgroupadd.ldif", 'w').close()
            addsecgroupldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/secgroupadd.ldif"
            result = request.form
            gidsearchcommand = os.popen(
                'sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b DC=grit,DC=ucsb,DC=edu \'(gidNumber=48***)\' | grep gidNumber')
            gidsearchresult = gidsearchcommand.read()
            gidresultstrip = re.sub(gidstrip, '', gidsearchresult)
            gidresultsplit = (gidresultstrip.split('\n'))
            maxgid = max(gidresultsplit)
            newgid = int(maxgid) + 1
            addsecgroup = f"""dn: CN={request.form['groupname']},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: group
description: {request.form['groupdesc']}
cn: {request.form['groupname']}
instanceType: 4
name: {request.form['groupname']}
sAMAccountName: {request.form['groupname']}
objectCategory: CN=Group,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
gidNumber: {newgid}
distinguishedName: CN={request.form['groupname']},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu"""
            with open("/tmp/secgroupadd.ldif", "a") as file:
                file.write(addsecgroup)
            file.close()
            writesecgroupldif = subprocess.Popen([addsecgroupldif], shell=True, stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT)
            ldif_secgroup_result = writesecgroupldif.stdout.read().decode()
            return render_template("access.html", result=result, ldif_secgroup_result=ldif_secgroup_result,
                                   newgid=newgid)
        ########################################################################################################################
        else:
            request.form['submit_button'] == 'submit AutoFS group'
            result = request.form
            grouplist = request.form.getlist('w3review')
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
            writeafsnewldif = subprocess.Popen([addafsnewldif], shell=True, stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT)
            ldif_afs_result = writeafsnewldif.stdout.read().decode()
            return render_template("access.html", result=result, ldif_afs_result=ldif_afs_result)
        return render_template("result.html", result=result, groups=grouplist)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)