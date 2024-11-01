import os
import re
from app.models.secgroup import SecurityGroup

secgroupregex = re.compile(r"(?<=^dn: CN=)[^,]+|(?<=^gidNumber: ).*$", re.MULTILINE)  # extract just the CN from the DN

def Convert(secgroups):
    res_dct = {secgroups[i]: secgroups[i + 1] for i in range(0, len(secgroups) - 1, 2)}
    return res_dct


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

def secgroups():
    secgroupcommand = os.popen(
        'sudo ldbsearch -H /var/lib/samba/private/sam.ldb -b "OU=GRIT Users,DC=grit,DC=ucsb,DC=edu" \'(sAMAccountType=268435456)\'')
    rawsecgroups = secgroupcommand.read()
    secgroups = secgroupregex.findall(rawsecgroups)
    secgroupdict = Convert(secgroups)
    return secgroupdict
