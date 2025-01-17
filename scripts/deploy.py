import ape
from ape import project, accounts


def deploy():
    signer = accounts.load("v3_deployer")

    signer.deploy(
        project.V3Router,
        "0x5B977577Eb8a480f63e11FC615D6753adB8652Ae",  # V2 Vault
        "0xb3F14E3fda2147fa7574fd003BA40Df266E0B90c",  # V3 Vault
        "V3 Aave V3 Router",
        max_priority_fee="0.000001 gwei",
        max_fee="15 gwei",
        publish=True,
    )


def main():
    deploy()
