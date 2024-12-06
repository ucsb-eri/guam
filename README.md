GUAM (GRIT User and Access Manager)
GUAM is a front end for samba-tool to aid in AD account creation, as well as manage NFS storage, and AutoFS mounts.

# Config

Guam searches for a configuration file `config.toml` in the the server root (`/opt/grit/guam2/` for production)

It will also replace environment variables defined in `.env`, and referenced in `config.toml` (this is not part of the TOML spec).

Note: It will not replace any environment variable, only ones defined in `.env`

# Development

### OS Dependencies

You will need to install the following tools locally

- `samba`
- `ldb`

### Python Dependencies

The dependencies are listed in `requirements.txt`, you can install them by running the following command:

`pip install -r requirements.txt`

The Samba API is installed with samba, there is no python package. Because of this, you need to ensure that the directory is in the `PYTHONPATH`.

```bash
export PYTHONPATH=/usr/lib/python3/dist-packages:$PYTHONPATH
```


