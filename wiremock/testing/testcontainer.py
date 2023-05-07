import os
from contextlib import contextmanager
from dataclasses import dataclass

import docker
import requests
from testcontainers.core.container import DockerContainer
from testcontainers.core.exceptions import ContainerStartException
from testcontainers.core.waiting_utils import wait_for_logs


@dataclass
class WireMockServer:
    port: str
    url: str


@contextmanager
def start_wiremock_container(mapping=None, port=None):
    """
    Start a wiremock test container using Testcontainers and set up mappings.

    :param mapping: Optional dict of wiremock mappings to set up.
    :param port: Optional port to use for the wiremock container. Defaults to 8080.
    :return: URL of the running wiremock container.
    """

    # TODO @mike - remove this docker in docker stuff.
    os.environ["DOCKER_HOST"] = "unix:///var/run/docker.sock"
    port = port or 8080
    client = docker.from_env()
    try:
        container = (
            DockerContainer("rodolpheche/wiremock")
            .with_env("JAVA_OPTS", "-Djava.net.preferIPv4Stack=true")
            .with_command("--no-request-journal")
            .with_volume_mapping("/var/run/docker.sock", "/var/run/docker.sock")
            .with_exposed_ports(port)
            .with_bind_ports(port)
        )
        with container:
            wait_for_logs(container, "Container started", timeout=120, interval=1)
            yield container
    except ContainerStartException as e:
        raise Exception("Error starting wiremock container") from e
    except requests.exceptions.RequestException as e:
        raise Exception("Error connecting to wiremock container") from e
    finally:
        client.close()


def wiremock_container(mapping=None, port=None):
    """
    Decorator that starts a wiremock test container using Testcontainers and sets up mappings.

    :param mapping: Optional dict of wiremock mappings to set up.
    :param port: Optional port to use for the wiremock container. Defaults to 8080.
    """

    def decorator(fn):
        def wrapper(*args, **kwargs):
            with start_wiremock_container(mapping=mapping, port=port) as container:
                container_port = container.get_exposed_port(port)
                wiremock_url = (
                    f"http://{container.get_container_host_ip()}:{container_port}"
                )
                kwargs["wiremock_url"] = wiremock_url
                server = WireMockServer(port=container_port, url=wiremock_url)
                return fn(server, *args, **kwargs)

        return wrapper

    return decorator
