#!/usr/local/bin/python3
"""Script to work with jupyter notebooks.

Will require notebook server token (possibly store this by setting environment variable on server start)

Will use [server api](https://github.com/jupyter/jupyter/wiki/Jupyter-Notebook-Server-API)

Things I want this to do:

* List existing kernels
* Join one of the existing kernels
    * With a terminal
    * With a notebook
"""

import json
from subprocess import run, PIPE
import requests
from pathlib import Path
from functools import singledispatch


class ServerInterface(object):
    def __init__(self, data):
        self._data = data
        self.url = data["url"]
        self.token = data["token"]
        self.notebook_dir = data["notebook_dir"]

    def running_kernels(self):
        full_url = f"{self.url}api/sessions?token={self.token}"
        return requests.get(full_url).json()


# TODO Will fail if more than one server is running.
def running_server() -> ServerInterface:
    """
    Returns object describing running server.
    """
    p = run(["jupyter", "notebook", "list", "--json"], stdout=PIPE)
    procs = list(map(json.loads, p.stdout.decode("utf-8").split("\n")[:-1]))
    procs = list(filter(lambda x: x["notebook_dir"].startswith("/Users/isaac"), procs))
    if len(procs) == 1:
        return ServerInterface(procs[0])
    elif len(procs) == 0:
        raise OSError("No jupyter servers under /Users/isaac could be found!")
    else:
        raise NotImplementedError(
            f"{len(procs)} servers found! Not able to tell which one to use."
        )


def show_running_kernels(kernels):
    report = ""
    paths = [x["path"] for x in kernels]
    names = [Path(x).stem for x in paths]
    kerneltype = [x["kernel"]["name"] for x in kernels]
    #     last_activity # Include for sorting?
    namemaxlength = max(len(x) for x in names)
    namemaxlength = max(namemaxlength, len("KernelName"))
    typemaxlength = max(len(x) for x in kerneltype)
    typemaxlength = max(typemaxlength, len("Kernel"))
    topline = "{}\t{}".format(
        "KernelName".ljust(namemaxlength), "Kernel".ljust(typemaxlength)
    )
    sep = "-" * (len(topline) + 2)
    report += f"{topline}\n"
    report += f"{sep}\n"
    for i in range(0, len(names)):
        report += "{}\t{}\n".format(
            names[i].ljust(namemaxlength), kerneltype[i].ljust(typemaxlength)
        )
    return report


def kernel_lookup(kernels, name):
    matching_kernels = []
    for kernel in kernels:
        if Path(kernel["path"]).stem == name:
            matching_kernels.append(kernel)
    if len(matching_kernels) == 0:
        raise Exception(f"No kernels with name '{name}' found.")
    elif len(matching_kernels) > 1:
        raise Exception(f"More than one kernel with name '{name}' found.")
    return matching_kernels[0]


# TODO, should this also start a kernel?
def create_notebook(path):
    s = running_server()
    surl = s.url
    token = s.token
    r = requests.put(
        f"{surl}api/contents/{str(path)}?token={token}", json={"format": "json"}
    )
    if r.status_code != 201:
        raise Exception(
            f"Could not create notebook at {path}. \n Recieved error: {r.status_code} for: {r.content}"
        )
    return r


def format_kernel_json(kernel_dict):
    return f"kernel-{kernel_dict['kernel']['id']}.json"


import click


@click.group()
def cli():
    pass


@cli.command(name="list", help="List running kernels")
def list_kernels():
    s = running_server()
    click.echo(show_running_kernels(s.running_kernels()))


@cli.command(name="join", help="Join an existing kernel by name")
@click.argument("name")
@click.option("-n", "--notebook", is_flag=True)
def join_kernel(name, notebook):
    """Join running kernel by notebook name."""
    s = running_server()
    kernels = s.running_kernels()
    to_join = kernel_lookup(kernels, name)
    if notebook:
        command = ["open", f"{s['url']}notebooks/{to_join['path']}"]
    elif not notebook:
        command = ["jupyter", "console", "--existing", format_kernel_json(to_join)]
    run(command)


@cli.command(name="open", help="Open jupyter notebook browser at path.")
@click.argument("path", required=False)
def open_browser(path=None):
    s = running_server()
    if path is None:
        path = "."

    abs_path = Path(path).absolute()
    rel_path = abs_path.relative_to(s.notebook_dir)

    if abs_path.is_dir():
        url = f"{s.url}tree/{rel_path}"
    elif abs_path.is_file() and abs_path.suffix == ".ipynb":
        url = f"{s.url}notebooks/{rel_path}"
    else:
        raise ValueError(f"Unable to open notebook at {abs_path}")

    run(["open", url])


if __name__ == "__main__":
    cli()
