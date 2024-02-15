import ape
from ape import project, accounts


def deploy():
    signer = accounts.load("v3_deployer")

    signer.deploy(
        project.V3Router,
        "",  # V2 Vault
        "",  # V3 Vault
        gas="3_000_000",
        max_priority_fee="0.000001 gwei",
        max_fee="35 gwei",
        publish=True,
    )


def main():
    deploy()
