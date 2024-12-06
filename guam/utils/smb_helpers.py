from samba.samdb import SamDB


def get_max_gid(samdb: SamDB):
    result = samdb.search("DC=grit,DC=ucsb,DC=edu",
                          expression="(gidNumber=48***)")
    max_gid = 0
    for item in result:
        gid = int(str(item.get("gidNumber", 0)))
        if gid > max_gid:
            max_gid = gid

    return max_gid


def get_max_uid(samdb: SamDB):
    result = {}

    result = samdb.search("DC=grit,DC=ucsb,DC=edu",
                          expression="(uidNumber=5****)")

    max_uid = 0
    for item in result:
        uid = int(str(item.get("uidNumber", 0)))
        if uid > max_uid:
            max_uid = uid

    return max_uid
