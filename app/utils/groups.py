import os
import re

from samba.samdb import SamDB

from app.models.secgroup import SecurityGroup

# def max_gid():


def get_max_gid(samdb: SamDB):
    result = samdb.search("DC=grit,DC=ucsb,DC=edu",
                          expression="(gidNumber=48***)")
    max_gid = 0
    for item in result:
        gid = int(str(item.get("gidNumber", 0)))
        if gid > max_gid:
            max_gid = gid

    return max_gid


def add_sec_group(samdb: SamDB, group: SecurityGroup):
    max_gid = get_max_gid(samdb)
    new_gid = max_gid + 1

    try:
        addsecgroup = f"""dn: CN={group.groupname},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: group
description: {group.groupdesc}
cn: {group.groupname}
instanceType: 4
name: {group.groupname}
sAMAccountName: {group.groupname}
objectCategory: CN=Group,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
gidNumber: {new_gid}
distinguishedName: CN={group.groupname},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu"""

        samdb.add_ldif(addsecgroup)

    except:
        samdb.transaction_cancel()
        raise
    else:
        samdb.transaction_commit()

    return group


def secgroups(samdb: SamDB, filter: str):
    search_result = samdb.search(
        "OU=GRIT Users,DC=grit,DC=ucsb,DC=edu", expression="(sAMAccountType=268435456)"
    )

    secgroupdict = {}

    for item in search_result:
        match = re.search("CN=(.*?),", str(item.get("dn", "")))
        group_name = match[1]
        gid = str(item.get("gidNumber", None))

        secgroupdict[group_name] = gid

    return secgroupdict
