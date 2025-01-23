import re

from paramiko.client import SSHClient, WarningPolicy
from samba.samdb import SamDB

from guam.models.autofs import AutoFSGroup, AutoFSMount


class NFSError(Exception):
    pass


def ssh_remote_command(host, cmd):
    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(WarningPolicy)
    client.connect(host, username="gritadm")
    stdin, stdout, stderr = client.exec_command(cmd)

    stdout_str = stdout.read().decode("ascii")
    stderr_str = stderr.read().decode("ascii")

    if len(stderr_str) > 0:
        raise NFSError(stderr_str)

    return stdout_str


def create_zfs_mount(hostname, zfspath, afspath, uid, gid):
    cmd = f"""
sudo zfs create {zfspath} && \
sudo zfs set quota=300g refquota=50g {zfspath} && \
sudo chown {uid}:{gid} {afspath}"""

    ssh_remote_command(hostname, cmd)


def create_exports(hostname, afspath):
    cmd = f"""
sudo bash -c 'cat <<EOF >> /etc/exports
{afspath} \
128.111.100.0/23(rw,no_root_squash) \
128.111.236.0/24(rw,no_root_squash) \
128.111.104.0/24(rw,no_root_squash)
EOF' && \
sudo systemctl restart nfs-server
"""
    ssh_remote_command(hostname, cmd)


def add_autofs_filesystem(username, afsserver, uid, gid, create_mount=True):
    print(afsserver)
    zfsserverpath = re.sub(".*:\/", "", afsserver)
    afsserverpath = re.sub("^.*:", "", afsserver)
    autofsserver = re.sub(":.*$", "", afsserver)

    zfspath = f"{zfsserverpath}{username}"
    afspath = f"{afsserverpath}{username}"

    if create_mount:
        create_zfs_mount(autofsserver, zfspath, afspath, uid, gid)
    create_exports(autofsserver, afspath)


def addAutofsEntry(samdb: SamDB, mount: AutoFSMount):
    samdb.transaction_start()
    try:
        for afs in mount.afsgroups:
            y = afs.strip("auto.")
            vers = 3 if y == "SMB" else 4

            addafsgroup = f"""dn: CN={mount.autofsmountpoint},CN={afs},OU={y.replace("-home", "")},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: {mount.autofsmountpoint}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: {mount.autofsmountpoint}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: {afs}
nisMapEntry: -nolock,rw,soft,vers={vers} {mount.autofspath}
distinguishedName: CN={mount.autofsmountpoint},CN={afs},OU={y.replace("-home", "")},OU=AutoFS,DC=grit,DC=ucsb,DC=edu"""

            samdb.add_ldif(addafsgroup)

    except Exception as e:
        samdb.transaction_cancel()
        raise
    else:
        samdb.transaction_commit()

    return mount


def addAutofsGroup(samdb: SamDB, groups: AutoFSGroup):
    grouplist = str(groups.groups).split("\r\n")

    samdb.transaction_start()
    try:
        for each in grouplist:
            each = each.strip()
            afsnewgroup = f"""dn: OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: organizationalUnit
ou: {each}
instanceType: 4
name: {each}
objectCategory: CN=Organizational-Unit,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
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
distinguishedName: CN=/-,CN=auto.master,OU={each},OU=AutoFS,DC=grit,DC=ucsb,DC=edu

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

            samdb.add_ldif(afsnewgroup)

    except Exception as e:
        samdb.transaction_cancel()
        raise
    else:
        samdb.transaction_commit()

    return grouplist


def afsgroups(samdb: SamDB, filter: str):
    result = samdb.search(
        "ou=AutoFS,DC=grit,DC=ucsb,DC=edu", expression=f"(nisMapName={filter}*)"
    )
    afsgroups = []
    for item in result:
        if "nisMapName" in item:
            afsgroup = str(item["nisMapName"])

            if afsgroup != "auto.master" and afsgroup not in afsgroups:
                afsgroups.append(afsgroup)

    return afsgroups
