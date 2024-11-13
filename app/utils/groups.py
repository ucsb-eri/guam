import os
import re

from samba.samdb import SamDB

from app.models.secgroup import SecurityGroup

# def max_gid():


def add_sec_group(group: SecurityGroup):
    open("/tmp/secgroupadd.ldif", 'w').close()
    addsecgroupldif = "sudo ldbadd -H /var/lib/samba/private/sam.ldb /tmp/secgroupadd.ldif"
    gidsearchcommand = os.popen('sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b DC=grit,DC=ucsb,DC=edu \'(gidNumber=48***)\' | grep gidNumber' )
    gidsearchresult = gidsearchcommand.read()
    gidresultstrip = re.sub(gidstrip, '', gidsearchresult)
    gidresultsplit = (gidresultstrip.split('\n'))
    maxgid = max(gidresultsplit)
    newgid = int(maxgid)+1
    addsecgroup = f"""dn: CN={group.groupname},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: group
description: {group.groupdesc}
cn: {group.groupname}
instanceType: 4
name: {group.groupname}
sAMAccountName: {group.groupname}
objectCategory: CN=Group,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
gidNumber: {newgid}
distinguishedName: CN={group.groupname},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu"""
    with open("/tmp/secgroupadd.ldif", "a") as file:
        file.write(addsecgroup)
    file.close()
    # writesecgroupldif = subprocess.Popen([addsecgroupldif], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # ldif_secgroup_result = writesecgroupldif.stdout.read().decode()
    # result = "form input: " + str(result) + " ldif command output: " + ldif_secgroup_result + " newgid: " + str(newgid)
    return group

def secgroups(samdb: SamDB, filter=""):
    search_result = samdb.search('OU=GRIT Users,DC=grit,DC=ucsb,DC=edu', expression="(sAMAccountType=268435456)")

    secgroupdict = {}

    for item in search_result:
        match = re.search('CN=(.*?),', str(item.get('dn', '')))
        group_name = match[1]
        gid = str(item.get('gidNumber', None))

        secgroupdict[group_name] = gid

    return secgroupdict
