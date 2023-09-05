import pytest
from ape import Contract, project


@pytest.fixture
def gov(accounts):
    yield accounts["0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52"]


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts["0x6Ba1734209a53a6E63C39D4e36612cc856A34D56"]


@pytest.fixture
def keeper(accounts):
    yield accounts["0x736D7e3c5a6CB2CE3B764300140ABF476F6CFCCF"]


@pytest.fixture
def token(dai):
    yield dai


@pytest.fixture 
def whale(accounts):
    # In order to get some funds for the token you are about to use,
    # it impersonate an exchange address to use it's funds.
    yield accounts["0x6B175474E89094C44Da98b954EedeAC495271d0F"]


@pytest.fixture
def amount(token, user, whale):
    amount = 100 * 10 ** token.decimals()

    token.transfer(user, amount, sender=whale)
    yield amount


@pytest.fixture
def dai():
    token_address = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    yield Contract(token_address)


@pytest.fixture
def v3_strategy(token, strategist):
    # v3_strategy = strategist.deploy(project.MockV3Strategy, token, "Mock V3 Strategy")
    v3_strategy = project.IStrategyInterface.at("0x9CeDB174BD547f9a0f99Dca63660710d59B75AD4")
    yield v3_strategy


@pytest.fixture
def vault(gov, rewards, guardian, management, token):
    vault = guardian.deploy(project.dependencies["yearnV2"]["0.4.6"].Vault)
    vault.initialize(token, gov, rewards, "", "", guardian, management, sender=gov)
    vault.setDepositLimit(2**256 - 1, sender=gov)
    vault.setManagement(management, sender=gov)
    yield vault


@pytest.fixture
def strategy(strategist, v3_strategy, keeper, vault, gov, token):
    strategy = strategist.deploy(project.V3Router, vault, v3_strategy)
    strategy.setKeeper(keeper, sender=strategist)
    vault.addStrategy(strategy, 10_000, 0, 2**256 - 1, 0, sender=gov)
    yield strategy


@pytest.fixture(scope="session")
def RELATIVE_APPROX():
    yield 1e-5
