# GUAM (GRIT User and Access Manager)

GUAM is a front end for samba-tool to aid in AD account creation, as well as manage NFS storage, and AutoFS mounts.

## Config

Guam searches for a configuration file `config.toml` in the following locations:

- `$XDG_CONFIG_HOME`, which defaults to: `/$HOME/.config/guam/config.toml`
- `/etc/guam/config.toml`

## Dependencies

- `samba`
- `ldb`

The Samba Python API is installed with samba, there is no external python package. Because of this, you need to ensure that the installation directory is in the `PYTHONPATH`.

For ubuntu, this is:

```bash
export PYTHONPATH=/usr/lib/python3/dist-packages:$PYTHONPATH
```

## Development

The application is built with `flit`, you need to install it first:

```
pip install flit
```

For development, install, guam by  running:

```
flit install -s
```

This symlinks the `guam` binary, to the development files.

### Systemd

There is currently no automation to copy the Systemd unit file when installing guam. You can manually copy `systemd/guam.service` from this repo, to  `/etc/systemd/system/guam.service` on the production server.
