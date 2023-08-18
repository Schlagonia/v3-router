import ape
from ape import project, accounts

def deploy():
    signer = accounts.load("v3_deployer")

    signer.deploy(
        project.V3Router,
        "0xdA816459F1AB5631232FE5e97a05BBBb94970c95", # DAI vault
        "0x9CeDB174BD547f9a0f99Dca63660710d59B75AD4", # Tokenized DSR
        gas="3_000_000",
        max_priority_fee="0.000001 gwei", 
        max_fee="35 gwei",
        publish=True
    )

def main():
    deploy()