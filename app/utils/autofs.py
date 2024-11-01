import os
import re

from app.models.autofs import AutoFSMount, AutoFSGroup

import subprocess


def addAutofsEntry(mount: AutoFSMount):
    result = form_data
    open("/tmp/afsgroupadd.ldif", "w").close()
    addafsldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/afsgroupadd.ldif"
    for afs in afsgroup:
        y = afs.strip("auto.")
        addafsgroup = f"""dn: CN={mount.autofsmountpoint},CN={afs},OU={y.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: {mount.autofsmountpoint}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: {mount.autofsmountpoint}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: {afs}
nisMapEntry: -nolock,rw,soft,vers=4 {mount.autofspath}
distinguishedName: CN={mount.autofsmountpoint},CN={afs},OU={y.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu"""
        with open("/tmp/afsgroupadd.ldif", "a") as file:
            file.write(addafsgroup)
    file.close()
    writeafsldif = subprocess.Popen(
        [addafsldif], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # ldif_afs_result = writeafsldif.stdout.read().decode()
    # result = (
    #     "form input: " + str(result) + " ldif command output: " + str(ldif_afs_result)
    # )
    return mount


def addAutofsGroup(groups: AutoFSGroup):
    print(groups)
    " ".join(str(e) for e in groups)
    grouplist = str(groups).split(r"\r\n")
    grouplist = [s.replace("[", "") for s in grouplist]
    grouplist = [s.replace("]", "") for s in grouplist]
    grouplist = [s.replace("'", "") for s in grouplist]
    open("/tmp/afsgroupnew.ldif", "w").close()
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
    writeafsnewldif = subprocess.Popen(
        [addafsnewldif], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    # ldif_afs_result = writeafsnewldif.stdout.read().decode()
    # result = (
    #     "form input: " + str(result) + " ldif command output: " + str(ldif_afs_result)
    # )
    return groups


def afsusergroups():  # define the data to be sent to the webui containing the list of existing autofs groups in AD
    # regex to filter out autofs map names from ldbsearch, ie auto.chc or auto.grit
    group = re.compile(r"(?<=^nisMapName: ).*$", re.MULTILINE)

    stream = os.popen(
        "sudo ldbsearch -H  /var/lib/samba/private/sam.ldb -b ou=AutoFS,DC=grit,DC=ucsb,DC=edu"
    )
    output = stream.read()
    rawafsgroups = group.findall(output)
    dedupafsgroups = list(dict.fromkeys(rawafsgroups))
    dedupafsgroups.remove("auto.master")
    afsgroups = dedupafsgroups
    afsusergroups = dedupafsgroups

    return afsusergroups
