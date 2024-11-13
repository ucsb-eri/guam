import os
import re
import subprocess

from samba.samdb import SamDB

from app.models.autofs import AutoFSGroup, AutoFSMount


def addAutofsEntry(samdb: SamDB, mount: AutoFSMount):
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
    " ".join(str(e) for e in groups)
    grouplist = str(groups).split(r"\r\n")
    grouplist = [s.replace("[", "") for s in grouplist]
    grouplist = [s.replace("]", "") for s in grouplist]
    grouplist = [s.replace("'", "") for s in grouplist]
    open("/tmp/afsgroupnew.ldif", "w").close()
    addafsnewldif = (
        "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/afsgroupnew.ldif"
    )
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


def afsgroups(samdb: SamDB, filter: str):
    result = samdb.search("ou=AutoFS,DC=grit,DC=ucsb,DC=edu", expression=f"(nisMapName={filter}*)")
    afsgroups = []
    for item in result:
        if "nisMapName" in item:
            afsgroup = str(item["nisMapName"])

            if afsgroup != "auto.master" and afsgroup not in afsgroups:
                afsgroups.append(afsgroup)

    return afsgroups
