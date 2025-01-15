from samba.samdb import SamDB

from guam.models.autofs import AutoFSGroup, AutoFSMount


def addAutofsEntry(samdb: SamDB, mount: AutoFSMount):
    samdb.transaction_start()
    try:
        for afs in mount.afsgroups:
            y = afs.strip("auto.")
            vers = 3 if y == "SMB" else 4

            addafsgroup = f"""dn: CN={mount.autofsmountpoint},CN={afs},OU={y.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu
objectClass: top
objectClass: nisObject
cn: {mount.autofsmountpoint}
instanceType: 4
showInAdvancedViewOnly: TRUE
name: {mount.autofsmountpoint}
objectCategory: CN=NisObject,CN=Schema,CN=Configuration,DC=grit,DC=ucsb,DC=edu
nisMapName: {afs}
nisMapEntry: -nolock,rw,soft,vers={vers} {mount.autofspath}
distinguishedName: CN={mount.autofsmountpoint},CN={afs},OU={y.replace('-home', '')},OU=AutoFS,DC=grit,DC=ucsb,DC=edu"""

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
