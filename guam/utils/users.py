import logging
import re
import secrets

from paramiko.client import SSHClient
from samba.samdb import SamDB
from .smb_helpers import get_max_uid

from guam.models.user import User
from guam.utils import groups

logger = logging.getLogger("uvicorn.error")
pw_length = 10
uidstrip = re.compile(r"^uidNumber: ", re.MULTILINE)


class NFSError(Exception):
    pass


def add_autofs_mount(user, uid, gid):
    zfsserverpath = re.sub(".*:\/", "", user.userafsserver)
    afsserverpath = re.sub("^.*:", "", user.userafsserver)
    autofsserver = re.sub(":.*$", "", user.userafsserver)

    nfscommand = f"""
sudo zfs create {zfsserverpath}{user.username} && \
sudo zfs set quota=300g refquota=50g {zfsserverpath}{user.username} && \
sudo chown {uid}:{gid} {afsserverpath}{user.username} && \
sudo bash -c 'cat <<EOF >> /etc/exports
{afsserverpath}{user.username} \
128.111.100.0/23(rw,no_root_squash) \
128.111.236.0/24(rw,no_root_squash) \
128.111.104.0/24(rw,no_root_squash)
EOF' && \
sudo systemctl restart nfs-server
"""
    client = SSHClient()
    client.load_system_host_keys()
    client.connect(autofsserver, username="gritadm")
    stdin, stdout, stderr = client.exec_command(nfscommand)

    stdout_str = stdout.read().decode("ascii")
    stderr_str = stderr.read().decode("ascii")

    if len(stderr_str) > 0:
        raise NFSError(stderr_str)


def afs_ldif(afs_mount, afs_group, afs_server, username, ou):
    autofs_settings = "-nolock,rw,soft,vers=4"
    return f"""dn: CN={afs_mount},CN={afs_group},OU={ou},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: {afs_mount}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: {afs_mount}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: {afs_group}
nisMapEntry: {autofs_settings} {afs_server}{username}
distinguishedName: CN={afs_mount},CN={afs_group},OU={ou},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
"""


def add_user(samdb: SamDB, user: User):
    max_uid = get_max_uid(samdb)
    newuid = int(max_uid) + 1
    secondary_gid = user.usersecgroup
    primary_gid = user.userprimarygroup
    gid = groups.secgroups(samdb).get(primary_gid)

    samdb.transaction_start()
    try:
        password = secrets.token_urlsafe(pw_length) + "!"
        samdb.newuser(
            username=user.username,
            password=password,
            userou="OU=GRIT Users",
            surname=user.lname,
            givenname=user.fname,
            uidnumber=newuid,
            gidnumber=gid,
            homedirectory=f"/home/{user.username}",
            loginshell="/bin/bash",
            department=user.department,
            description=user.description,
        )

        # Add properties that are not supported with the newuser command
        extra_props = f"""dn: CN={user.username},OU=GRIT Users,DC=grit,DC=ucsb,DC=edu
changetype: modify
add: mail
mail: {user.email}
-
add: unixHomeDirectory
unixHomeDirectory: /home/{user.username}

"""
        samdb.modify_ldif(extra_props)

        samdb.add_remove_group_members(
            groupname=user.userprimarygroup,
            members=[user.username],
            add_members_operation=True,
        )

        if secondary_gid:
            for j in secondary_gid:
                samdb.add_remove_group_members(
                    groupname=j, members=[
                        user.username], add_members_operation=True
                )

        usergroups = user.afsusergroup
        for i in usergroups:
            x = i.replace("auto.", "")

            add_userafs = afs_ldif(
                f"/home/{user.username}",
                i,
                user.userafsserver,
                user.username,
                x.replace("-home", ""),
            )
            samdb.add_ldif(add_userafs)

        add_userafs_all = afs_ldif(
            f"/home/{user.username}",
            "auto.ALL",
            user.userafsserver,
            user.username,
            "ALL",
        )
        samdb.add_ldif(add_userafs_all)

        add_userafs_nextcloud = afs_ldif(
            f"/var/www/nextcloud-data/{user.username}",
            "auto.Nextcloud",
            user.userafsserver,
            user.username,
            "Nextcloud",
        )
        samdb.add_ldif(add_userafs_nextcloud)

        add_autofs_mount(user, newuid, gid)

    except:
        samdb.transaction_cancel()
        raise
    else:
        samdb.transaction_commit()

    return user
